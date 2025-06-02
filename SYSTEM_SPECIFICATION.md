# Shift Scheduler システム仕様書
# Claude Code実装用

## 📋 プロジェクト概要

### システム名
Employee Shift Scheduler API

### 概要
Timefold Solverを使用した従業員シフト最適化システム。制約充足問題として複雑なシフト要件を解決し、労働基準法遵守と業務効率を両立する。

### 技術スタック
- **言語**: Python 3.11+
- **Webフレームワーク**: FastAPI
- **最適化エンジン**: Timefold Solver (Java 17)
- **パッケージマネージャー**: uv
- **開発環境**: Dev Container (Apple Silicon対応)
- **データベース**: メモリ内 (将来的にPostgreSQL対応)

---

## 🎯 機能要件

### 1. シフト最適化機能

#### 1.1 基本最適化
- **機能ID**: F001
- **説明**: 従業員とシフトのマッチング最適化
- **入力**: 従業員リスト、シフトリスト、制約条件
- **出力**: 最適化されたシフト割り当て
- **エンドポイント**: `POST /api/shifts/solve-sync`

#### 1.2 非同期最適化
- **機能ID**: F002
- **説明**: 大量データ対応の非同期処理
- **入力**: 従業員リスト、シフトリスト
- **出力**: ジョブID、処理状況
- **エンドポイント**: 
  - `POST /api/shifts/solve` (ジョブ投入)
  - `GET /api/shifts/solve/{job_id}` (結果取得)

#### 1.3 シフト固定機能
- **機能ID**: F003
- **説明**: 既決定シフトを固定して一部のみ最適化
- **入力**: シフトID、従業員ID、固定フラグ
- **出力**: 固定状況、再最適化結果
- **エンドポイント**:
  - `POST /api/shifts/pin` (シフト固定)
  - `POST /api/shifts/unpin` (固定解除)
  - `POST /api/shifts/re-optimize/{job_id}` (再最適化)

### 2. 週勤務時間分析機能

#### 2.1 勤務時間分析
- **機能ID**: F004
- **説明**: 従業員別週勤務時間分析と制約違反検出
- **入力**: シフトスケジュール
- **出力**: 週別勤務時間、制約違反、改善提案
- **エンドポイント**: `POST /api/shifts/analyze-weekly`

#### 2.2 コンプライアンスチェック
- **機能ID**: F005
- **説明**: 労働基準法等への準拠状況確認
- **出力**: 違反項目、重要度、推奨対応
- **エンドポイント**: `GET /api/shifts/test-weekly`

### 3. データ管理機能

#### 3.1 デモデータ提供
- **機能ID**: F006
- **説明**: テスト用のサンプルデータ生成
- **出力**: 1週間分の現実的なシフトデータ
- **エンドポイント**: `GET /api/shifts/demo`

---

## 🔒 制約仕様

### Hard Constraints (絶対遵守)

#### HC001: スキルマッチング制約
```python
制約名: required_skill_constraint
説明: シフトに必要なスキルを持つ従業員のみ割り当て可能
条件: shift.employee.skills ⊇ shift.required_skills
違反時: HardMediumSoftScore.ONE_HARD ペナルティ
```

#### HC002: シフト重複防止制約
```python
制約名: no_overlapping_shifts_constraint
説明: 同一従業員が同時刻に複数シフト割り当て禁止
条件: ∀(shift1, shift2) where shift1.employee = shift2.employee
      → ¬overlaps(shift1.time, shift2.time)
違反時: HardMediumSoftScore.ONE_HARD ペナルティ
```

#### HC003: 週最大勤務時間制約
```python
制約名: weekly_maximum_hours_constraint
説明: 従業員の週勤務時間上限(45時間)
条件: sum(employee.weekly_hours) ≤ 45 * 60 (分)
違反時: HardMediumSoftScore.ONE_HARD * 超過時間(時間単位)
```

### Medium Constraints (重要だが例外あり)

#### MC001: 最低休憩時間制約
```python
制約名: minimum_rest_time_constraint
説明: 連続シフト間の最低休憩時間(8時間)
条件: next_shift.start_time - current_shift.end_time ≥ 8時間
違反時: HardMediumSoftScore.ONE_MEDIUM ペナルティ
```

#### MC002: 週最小勤務時間制約
```python
制約名: weekly_minimum_hours_constraint
説明: フルタイム従業員の最小勤務時間(32時間)
条件: フルタイム従業員 → weekly_hours ≥ 32 * 60 (分)
違反時: HardMediumSoftScore.ONE_MEDIUM * 不足時間
```

### Soft Constraints (最適化目標)

#### SC001: 未割り当てシフト最小化
```python
制約名: minimize_unassigned_shifts_constraint
説明: 未割り当てシフトの最小化(優先度考慮)
目標: 全シフトの従業員割り当て
ペナルティ: HardMediumSoftScore.of_soft(shift.priority * 10)
```

#### SC002: 労働時間公平分配
```python
制約名: fair_workload_distribution_constraint
説明: 従業員間の勤務時間格差最小化
目標: 各従業員の勤務時間を8時間/日に近づける
ペナルティ: HardMediumSoftScore.ONE_SOFT * |actual_hours - 480分|
```

#### SC003: 週勤務時間目標達成
```python
制約名: weekly_hours_target_constraint
説明: 各従業員の目標勤務時間達成
目標: フルタイム40時間/週、パートタイム20時間/週
ペナルティ: HardMediumSoftScore.ONE_SOFT * |actual - target|
```

---

## 📊 データモデル仕様

### Employee (従業員)
```python
@dataclass
class Employee:
    id: str                    # 一意識別子
    name: str                  # 従業員名
    skills: Set[str]           # 保有スキル一覧
    
    # メソッド仕様
    has_skill(skill: str) -> bool
    has_all_skills(required_skills: Set[str]) -> bool
```

### Shift (シフト)
```python
@planning_entity
@dataclass  
class Shift:
    id: str                           # 一意識別子
    start_time: datetime              # 開始日時
    end_time: datetime                # 終了日時
    required_skills: Set[str]         # 必要スキル
    location: Optional[str]           # 勤務場所
    priority: int                     # 優先度(1-10, 1が最高)
    is_pinned: bool                   # 固定フラグ
    
    # Planning Variable (Timefold最適化対象)
    employee: Optional[Employee]      # 割り当て従業員
    
    # メソッド仕様
    get_duration_minutes() -> int
    overlaps_with(other: Shift) -> bool
    is_assigned() -> bool
    pin_assignment(employee: Employee) -> None
    unpin_assignment() -> None
```

### ShiftSchedule (スケジュール全体)
```python
@planning_solution
@dataclass
class ShiftSchedule:
    # Problem Facts (最適化で変更されない)
    employees: List[Employee]
    
    # Planning Entities (最適化対象)
    shifts: List[Shift]
    
    # Planning Score (最適化結果)
    score: HardMediumSoftScore
    
    # メソッド仕様
    get_pinned_shifts() -> List[Shift]
    get_optimizable_shifts() -> List[Shift]
    pin_shift(shift_id: str, employee_id: str) -> bool
    unpin_shift(shift_id: str) -> bool
```

---

## 🌐 API仕様

### Base URL
```
http://localhost:8000
```

### 認証
現在は認証なし（将来的にJWT実装予定）

### Content-Type
```
application/json
```

### 共通レスポンス形式
```json
{
  "success": boolean,
  "data": object,
  "message": string,
  "error": string,
  "timestamp": string
}
```

### エンドポイント一覧

#### 1. ヘルスチェック
```http
GET /health
Response: {"status": "UP", "service": "shift-scheduler"}
```

#### 2. デモデータ取得
```http
GET /api/shifts/demo
Response: ShiftScheduleResponse
```

#### 3. 同期シフト最適化
```http
POST /api/shifts/solve-sync
Request: ShiftScheduleRequest
Response: ShiftScheduleResponse
```

#### 4. 非同期シフト最適化
```http
POST /api/shifts/solve
Request: ShiftScheduleRequest  
Response: {"job_id": string, "status": "SOLVING_SCHEDULED"}

GET /api/shifts/solve/{job_id}
Response: SolutionResponse
```

#### 5. シフト固定機能
```http
POST /api/shifts/pin
Request: {"shift_id": string, "employee_id": string}
Response: PinningResponse

POST /api/shifts/unpin  
Request: {"shift_id": string}
Response: PinningResponse

GET /api/shifts/pinning-status/{job_id}
Response: PinningStatusResponse
```

#### 6. 週勤務時間分析
```http
POST /api/shifts/analyze-weekly
Request: ShiftScheduleRequest
Response: WeeklyAnalysisResponse

GET /api/shifts/test-weekly
Response: WeeklyTestResponse
```

---

## 🏗️ アーキテクチャ仕様

### システム構成
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Timefold      │    │   Data Models   │
│   (Web Layer)   │────│   Solver        │────│   (Domain)      │
│                 │    │   (Optimization)│    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────│   Constraints   │──────────────┘
                        │   (Business     │
                        │    Logic)       │
                        └─────────────────┘
```

### ディレクトリ構造
```
shift-scheduler/
├── main.py                  # FastAPI application entry point
├── models.py                # Data models and Pydantic schemas  
├── constraints.py           # Timefold constraint definitions
├── pyproject.toml          # uv configuration and dependencies
├── .devcontainer/          # Dev Container configuration
├── .vscode/                # VS Code settings and debug config
├── api-test.http           # REST client test cases
└── test_models.py          # Unit tests
```

### 依存関係
```toml
[dependencies]
fastapi = ">=0.104.1"           # Web framework
uvicorn = ">=0.24.0"            # ASGI server  
timefold = ">=1.14.0"           # Optimization solver
pydantic = ">=2.5.0"            # Data validation
python-multipart = ">=0.0.6"   # Form data support
```

---

## 🧪 テスト仕様

### テスト戦略
- **Unit Tests**: 各クラス・メソッドの単体テスト
- **Integration Tests**: API エンドポイントのテスト
- **Constraint Tests**: 制約ロジックの検証
- **Performance Tests**: 最適化処理の性能テスト

### テストデータ
```python
# 標準テストデータセット
employees = [
    Employee("emp1", "田中太郎", {"看護師", "CPR", "フルタイム"}),
    Employee("emp2", "佐藤花子", {"看護師", "フルタイム"}), 
    Employee("emp3", "鈴木一郎", {"警備員", "フルタイム"}),
    Employee("emp4", "高橋美咲", {"受付", "事務", "パートタイム"})
]

shifts = [
    # 1週間分のリアルなシフトパターン
    # 朝シフト、夜シフト、警備シフト、受付シフト
]
```

### テスト実行
```bash
# 全テスト実行
make test

# カバレッジ付きテスト
uv run pytest --cov=.

# 特定テスト実行  
uv run pytest test_models.py::test_employee_creation
```

---

## 🚀 デプロイ仕様

### 開発環境
- **Dev Container**: Apple Silicon Mac対応
- **ホットリロード**: uvicorn --reload
- **デバッグ**: VS Code統合デバッガー

### 本番環境
- **コンテナ**: Docker (マルチプラットフォーム対応)
- **プロセス管理**: uvicorn (複数ワーカー)
- **リバースプロキシ**: Nginx (将来予定)
- **データベース**: PostgreSQL (将来予定)

### 環境変数
```bash
# 本番環境用
ENVIRONMENT=production
LOG_LEVEL=info
DATABASE_URL=postgresql://user:pass@host:port/db
JWT_SECRET_KEY=secret
TIMEFOLD_SOLVER_TIMEOUT=60s
```

---

## 📈 パフォーマンス要件

### レスポンス時間
- **同期最適化**: 30秒以内 (中規模データ)
- **API レスポンス**: 200ms以内 (データ取得)
- **週勤務時間分析**: 5秒以内

### スケーラビリティ
- **従業員数**: 最大1000人
- **シフト数**: 最大10000シフト/月
- **同時リクエスト**: 100req/sec

### メモリ使用量
- **ベースライン**: 512MB
- **最適化実行時**: 2GB以内
- **Java Heap**: 1GB (Timefold Solver用)

---

## 🔒 セキュリティ仕様

### 認証・認可 (将来実装)
- **認証方式**: JWT Bearer Token
- **ロール**: Admin, Manager, Employee
- **権限**: Read, Write, Execute

### データ保護
- **入力検証**: Pydantic による厳密な型チェック
- **SQL Injection**: ORM使用により対策済み
- **XSS**: FastAPI自動エスケープ

### ログ・監査
- **アクセスログ**: uvicorn標準ログ
- **操作ログ**: シフト固定・解除の履歴
- **エラーログ**: 構造化ログ出力

---

## 🔄 今後の拡張計画

### Phase 2: データベース統合
- PostgreSQL導入
- データ永続化
- 履歴管理

### Phase 3: 認証・権限管理
- JWT認証
- ロールベースアクセス制御
- 組織階層対応

### Phase 4: 高度な機能
- 複数拠点対応
- 自動通知機能
- レポート生成
- CSV/Excel入出力

### Phase 5: 機械学習統合
- 需要予測
- パターン学習
- 自動調整提案

---

## 📞 開発・運用情報

### 開発チーム連絡先
- **Lead Developer**: [連絡先]
- **System Architecture**: [連絡先]  
- **QA Engineer**: [連絡先]

### リポジトリ情報
- **Git Repository**: [URL]
- **CI/CD Pipeline**: [URL]
- **Documentation**: [URL]

### サポート・トラブルシューティング
- **Issue Tracker**: [URL]
- **Knowledge Base**: [URL]
- **Emergency Contact**: [連絡先]

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-06-02  
**Next Review**: 2025-07-02