# MCP Employee Management Sequence Diagram

Sequence diagram for employee management functionality accessed from Claude Desktop.

```mermaid
sequenceDiagram
    participant User as User
    participant CD as Claude Desktop
    participant MCP as MCP Server
    participant API as ShiftAgent API
    participant Solver as Timefold Solver

    Note over User,Solver: 1. Initial Schedule Optimization

    User->>CD: Request schedule optimization
    CD->>MCP: solve_schedule_async()
    MCP->>API: POST /api/shifts/solve
    API->>Solver: Start async optimization
    API-->>MCP: Return job_id
    MCP-->>CD: Return job_id
    CD-->>User: Notify optimization started

    Note over User,Solver: 2. Check Optimization Results

    User->>CD: Want to check results
    CD->>MCP: get_solve_status(job_id)
    MCP->>API: GET /api/shifts/solve/{job_id}
    API-->>MCP: Optimization results
    MCP-->>CD: Schedule results
    CD-->>User: Display optimization results

    Note over User,Solver: 3. Add Employee (Resolve Constraint Violations)

    User->>CD: Add new employee to resolve<br/>constraint violations
    CD->>MCP: add_employee_to_job(job_id, employee)
    MCP->>API: POST /api/shifts/{job_id}/add-employee

    rect rgb(240, 248, 255)
        Note right of API: Pinning Strategy
        API->>API: 1. Pin valid assignments
        API->>API: 2. Unpin only constraint violations
        API->>API: 3. Add new employee
    end

    API->>Solver: Partial re-optimization
    Solver-->>API: Optimize with minimal changes
    API->>API: Unpin all shifts
    API-->>MCP: Update results
    MCP-->>CD: Addition success message
    CD-->>User: Employee added and<br/>constraint violations resolved

    Note over User,Solver: 4. Update Skills (Targeted Optimization)

    User->>CD: Update employee skills for<br/>better assignments
    CD->>MCP: update_employee_skills(job_id, employee_id, skills)
    MCP->>API: PATCH /api/shifts/{job_id}/employee/{employee_id}/skills

    rect rgb(255, 248, 240)
        Note right of API: Intelligent Pinning
        API->>API: 1. Analyze skill change impact
        API->>API: 2. Unpin improvable assignments
        API->>API: 3. Pin unaffected assignments
    end

    API->>Solver: Re-optimize affected areas only
    Solver-->>API: Update necessary parts only
    API->>API: Unpin all shifts
    API-->>MCP: Update results
    MCP-->>CD: Skill update success message
    CD-->>User: Skills updated and<br/>optimal assignments achieved

    Note over User,Solver: 5. Final Results Review

    User->>CD: Check final schedule
    CD->>MCP: get_schedule_shifts(job_id)
    MCP->>API: GET /api/shifts/solve/{job_id}
    API-->>MCP: Final schedule
    MCP-->>CD: Detailed schedule information
    CD-->>User: Display updated schedule
```

## Key Processing Flows

### 1. Pinning Strategy Details

```mermaid
graph TD
    A[Completed Job] --> B{Evaluate Each Shift}
    B --> C{Has Constraint Violation?}
    C -->|Yes| D[Unpin<br/>Target for Re-optimization]
    C -->|No| E[Pin<br/>Maintain Current State]
    D --> F[Execute Solver]
    E --> F
    F --> G[Optimization Complete]
    G --> H[Unpin All Shifts]
```

### 2. Impact Analysis for Skill Updates

```mermaid
graph LR
    A[Skill Update] --> B{Added Skills?}
    B -->|Yes| C[Explore newly available<br/>shifts]
    B -->|No| D{Removed Skills?}
    D -->|Yes| E[Unpin affected<br/>assignments]
    D -->|No| F[No Change]
    C --> G[Execute Optimization]
    E --> G
    F --> G
```

## Technical Highlights

1. **Asynchronous Processing**: Initial optimization runs async due to processing time
2. **Pinning Feature**: Leverages Timefold Solver's `@PlanningPin` annotation
3. **Minimal Changes**: Preserves existing valid assignments, re-optimizes only necessary parts
4. **MCP Integration**: Claude Desktop communicates with API through MCP tools

## Error Handling

- Job not found: 404 error
- Job not completed: 400 error
- Employee not found: 404 error
- Optimization failure: 500 error

## Architecture Benefits

### Intelligent Re-optimization
- **Employee Addition**: Focuses on unassigned shifts and constraint violation resolution
- **Skill Updates**: Recalculates only assignments affected by skill changes
- **Partial Optimization**: Processes only parts that need changes, not the entire schedule

### User Experience
- **Natural Language Interface**: Users can describe their needs in plain language
- **Real-time Feedback**: Immediate status updates and detailed results
- **Minimal Disruption**: Existing schedule remains stable while making targeted improvements

### Technical Excellence
- **Constraint Preservation**: Hard constraints always maintained
- **Performance Optimization**: Pinning reduces solver complexity
- **Scalability**: Partial re-optimization scales better than full recalculation
