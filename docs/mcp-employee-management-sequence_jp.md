# MCP Employee Management Sequence Diagram

Claude Desktopから従業員管理機能を利用する際のシーケンス図です。

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant CD as Claude Desktop
    participant MCP as MCP Server
    participant API as Shift Scheduler API
    participant Solver as Timefold Solver

    Note over User,Solver: 1. 初期スケジュール最適化

    User->>CD: スケジュール最適化を依頼
    CD->>MCP: solve_schedule_async()
    MCP->>API: POST /api/shifts/solve
    API->>Solver: 非同期で最適化開始
    API-->>MCP: job_id返却
    MCP-->>CD: job_id返却
    CD-->>User: 最適化開始を通知

    Note over User,Solver: 2. 最適化結果確認

    User->>CD: 結果を確認したい
    CD->>MCP: get_solve_status(job_id)
    MCP->>API: GET /api/shifts/solve/{job_id}
    API-->>MCP: 最適化結果
    MCP-->>CD: スケジュール結果
    CD-->>User: 最適化結果を表示

    Note over User,Solver: 3. 従業員追加（制約違反解消）

    User->>CD: 新しい従業員を追加して<br/>制約違反を解消したい
    CD->>MCP: add_employee_to_job(job_id, employee)
    MCP->>API: POST /api/shifts/{job_id}/add-employee

    rect rgb(240, 248, 255)
        Note right of API: Pinning戦略
        API->>API: 1. 有効な割り当てをpin
        API->>API: 2. 制約違反のみunpin
        API->>API: 3. 新従業員を追加
    end

    API->>Solver: 部分的な再最適化
    Solver-->>API: 最小限の変更で最適化
    API->>API: 全てのシフトをunpin
    API-->>MCP: 更新結果
    MCP-->>CD: 追加成功メッセージ
    CD-->>User: 従業員が追加され<br/>制約違反が解消されました

    Note over User,Solver: 4. スキル更新（ピンポイント最適化）

    User->>CD: 従業員のスキルを更新して<br/>より良い配置にしたい
    CD->>MCP: update_employee_skills(job_id, employee_id, skills)
    MCP->>API: PATCH /api/shifts/{job_id}/employee/{employee_id}/skills

    rect rgb(255, 248, 240)
        Note right of API: インテリジェントPinning
        API->>API: 1. スキル変更の影響分析
        API->>API: 2. 改善可能な割り当てをunpin
        API->>API: 3. 影響のない割り当てをpin
    end

    API->>Solver: 影響範囲のみ再最適化
    Solver-->>API: 必要な部分のみ更新
    API->>API: 全てのシフトをunpin
    API-->>MCP: 更新結果
    MCP-->>CD: スキル更新成功メッセージ
    CD-->>User: スキルが更新され<br/>最適な配置になりました

    Note over User,Solver: 5. 結果確認

    User->>CD: 最終的なスケジュールを確認
    CD->>MCP: get_schedule_shifts(job_id)
    MCP->>API: GET /api/shifts/solve/{job_id}
    API-->>MCP: 最終スケジュール
    MCP-->>CD: 詳細なスケジュール情報
    CD-->>User: 更新されたスケジュールを表示
```

## 主要な処理フロー

### 1. Pinning戦略の詳細

```mermaid
graph TD
    A[完了済みジョブ] --> B{各シフトの評価}
    B --> C{制約違反あり?}
    C -->|Yes| D[Unpin<br/>再最適化対象]
    C -->|No| E[Pin<br/>現状維持]
    D --> F[Solver実行]
    E --> F
    F --> G[最適化完了]
    G --> H[全シフトUnpin]
```

### 2. スキル更新時の影響分析

```mermaid
graph LR
    A[スキル更新] --> B{追加されたスキル?}
    B -->|Yes| C[新たに対応可能な<br/>シフトを探索]
    B -->|No| D{削除されたスキル?}
    D -->|Yes| E[影響を受ける<br/>割り当てをUnpin]
    D -->|No| F[変更なし]
    C --> G[最適化実行]
    E --> G
    F --> G
```

## 技術的なポイント

1. **非同期処理**: 初期の最適化は時間がかかるため非同期で実行
2. **Pinning機能**: Timefold Solverの`@PlanningPin`アノテーションを活用
3. **最小限の変更**: 既存の有効な割り当ては保持し、必要な部分のみ再最適化
4. **MCP統合**: Claude DesktopがMCPツールを通じてAPIと通信

## エラーハンドリング

- ジョブが見つからない場合: 404エラー
- ジョブが完了していない場合: 400エラー
- 従業員が見つからない場合: 404エラー
- 最適化に失敗した場合: 500エラー
