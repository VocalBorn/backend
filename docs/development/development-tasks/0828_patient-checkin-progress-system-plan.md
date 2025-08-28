# 患者端簽到與進度追蹤系統規劃文件

## 專案概述

本文件規劃 VocalBorn 語言治療學習平台中患者端簽到與進度追蹤系統的完整架構設計。該系統將提供遊戲化的簽到機制和全面的學習進度追蹤功能，以提升患者的參與度和學習動機。

---

## 1. 功能需求分析

### 1.1 簽到系統功能需求

#### 1.1.1 核心功能
- **每日簽到**：患者可以每日進行一次簽到
- **連續簽到追蹤**：記錄並顯示連續簽到天數
- **簽到獎勵機制**：提供連續簽到獎勵和里程碑獎勵
- **簽到歷史查詢**：提供簽到記錄的查詢功能

#### 1.1.2 獎勵機制（待確認具體需求）
- **積分系統**：每日簽到獲得基礎積分
- **連續簽到獎勵**：連續簽到天數越多，獎勵越豐富
- **里程碑獎勵**：達到特定簽到天數時的特殊獎勵
- **補簽機制**：是否允許補簽及補簽規則

#### 1.1.3 業務規則
- 每日簽到時間窗口：00:00 - 23:59（使用者所在時區）
- 連續簽到斷線重置規則
- 簽到與練習活動的關聯性（是否需要完成練習才能簽到）

### 1.2 進度追蹤系統功能需求

#### 1.2.1 核心功能
- **整體學習進度**：顯示所有情境章節的完成狀態
- **章節完成度統計**：每個章節內句子練習的完成比例
- **近期活動統計**：過去 7 日的練習活動摘要
- **學習時長統計**：累計和階段性的學習時間記錄
- **練習表現追蹤**：錄音次數、完成率等指標

#### 1.2.2 統計指標
- **過去 7 日統計**：
  - 完成的練習會話數量
  - 錄音的句子總數
  - 累計練習時長
  - 平均每日練習時長
- **總體統計**：
  - 已完成的章節數 / 總章節數
  - 已練習的句子數 / 總句子數
  - 累計學習天數
  - 總學習時長

### 1.3 使用者故事

#### 1.3.1 簽到相關使用者故事
1. **作為患者**，我希望能夠每日簽到以建立學習習慣
2. **作為患者**，我希望看到連續簽到天數以保持動機
3. **作為患者**，我希望獲得簽到獎勵以增加參與感
4. **作為患者**，我希望查看簽到歷史記錄
5. **作為治療師**，我希望能查看患者的簽到情況以了解其參與度

#### 1.3.2 進度追蹤相關使用者故事
1. **作為患者**，我希望清楚看到自己在各個章節的學習進度
2. **作為患者**，我希望了解自己近期的練習活動狀況
3. **作為患者**，我希望看到學習成就和里程碑
4. **作為治療師**，我希望監控患者的學習進度和活躍度

### 1.4 功能優先級

#### 高優先級 (P0)
- 每日簽到功能
- 連續簽到天數追蹤
- 基礎進度統計（章節完成度）
- 過去 7 日練習統計

#### 中優先級 (P1)
- 簽到獎勵機制
- 詳細的學習時長統計
- 練習表現追蹤
- 簽到歷史查詢

#### 低優先級 (P2)
- 補簽機制
- 進階獎勵系統
- 成就徽章系統
- 進度分享功能

---

## 2. API Router 規劃

### 2.1 簽到相關路由

```python
# 簽到路由組：/api/checkin
class CheckinRouter:
    
    @router.post("/daily")
    async def daily_checkin(current_user: User) -> CheckinResponse:
        """每日簽到"""
        pass
    
    @router.get("/status")
    async def get_checkin_status(current_user: User) -> CheckinStatusResponse:
        """取得今日簽到狀態和連續簽到天數"""
        pass
    
    @router.get("/history")
    async def get_checkin_history(
        current_user: User,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> CheckinHistoryResponse:
        """取得簽到歷史記錄"""
        pass
    
    @router.get("/rewards")
    async def get_available_rewards(current_user: User) -> RewardsResponse:
        """取得可領取的獎勵"""
        pass
    
    @router.post("/rewards/{reward_id}/claim")
    async def claim_reward(reward_id: uuid.UUID, current_user: User) -> RewardClaimResponse:
        """領取獎勵"""
        pass
```

### 2.2 進度追蹤相關路由

```python
# 進度追蹤路由組：/api/progress
class ProgressRouter:
    
    @router.get("/overview")
    async def get_progress_overview(current_user: User) -> ProgressOverviewResponse:
        """取得整體學習進度概覽"""
        pass
    
    @router.get("/chapters")
    async def get_chapters_progress(current_user: User) -> ChaptersProgressResponse:
        """取得所有章節的完成進度"""
        pass
    
    @router.get("/chapters/{chapter_id}")
    async def get_chapter_detail_progress(
        chapter_id: uuid.UUID,
        current_user: User
    ) -> ChapterDetailProgressResponse:
        """取得特定章節的詳細進度"""
        pass
    
    @router.get("/recent-activity")
    async def get_recent_activity(
        current_user: User,
        days: int = Query(7, ge=1, le=30)
    ) -> RecentActivityResponse:
        """取得近期活動統計"""
        pass
    
    @router.get("/statistics")
    async def get_learning_statistics(
        current_user: User,
        period: str = Query("all", regex="^(all|week|month|year)$")
    ) -> LearningStatisticsResponse:
        """取得學習統計數據"""
        pass
```

### 2.3 路由組織結構

```
src/
├── checkin/
│   ├── __init__.py
│   ├── router.py                 # 簽到相關路由
│   ├── models.py                 # 簽到相關資料模型
│   ├── schemas.py                # 簽到相關 Pydantic 模型
│   └── services/
│       ├── __init__.py
│       ├── checkin_service.py    # 簽到業務邏輯
│       └── reward_service.py     # 獎勵系統邏輯
├── progress/
│   ├── __init__.py
│   ├── router.py                 # 進度追蹤相關路由
│   ├── schemas.py                # 進度追蹤相關 Pydantic 模型
│   └── services/
│       ├── __init__.py
│       ├── progress_service.py   # 進度統計業務邏輯
│       └── statistics_service.py # 統計計算邏輯
```

---

## 3. Service 業務邏輯規劃

### 3.1 簽到服務 (CheckinService)

#### 3.1.1 核心方法

```python
class CheckinService:
    """簽到服務 - 使用函數式設計"""
    
    async def perform_daily_checkin(user_id: uuid.UUID) -> CheckinResult:
        """執行每日簽到
        
        業務邏輯：
        1. 驗證今日是否已簽到
        2. 計算連續簽到天數
        3. 記錄簽到記錄
        4. 觸發獎勵機制
        5. 更新使用者統計
        """
        pass
    
    async def get_checkin_status(user_id: uuid.UUID) -> CheckinStatus:
        """取得簽到狀態
        
        回傳資訊：
        - 今日是否已簽到
        - 連續簽到天數
        - 本月簽到天數
        - 下次獎勵還需幾天
        """
        pass
    
    async def calculate_consecutive_days(user_id: uuid.UUID) -> int:
        """計算連續簽到天數"""
        pass
    
    async def get_checkin_history(
        user_id: uuid.UUID,
        start_date: date,
        end_date: date,
        page: int,
        page_size: int
    ) -> PaginatedCheckinHistory:
        """取得簽到歷史"""
        pass
```

#### 3.1.2 獎勵服務 (RewardService)

```python
class RewardService:
    """獎勵服務 - 使用函數式設計"""
    
    async def calculate_checkin_rewards(consecutive_days: int) -> List[Reward]:
        """根據連續簽到天數計算獎勵"""
        pass
    
    async def grant_reward(user_id: uuid.UUID, reward_type: str, amount: int):
        """發放獎勵"""
        pass
    
    async def get_available_rewards(user_id: uuid.UUID) -> List[AvailableReward]:
        """取得可領取的獎勵"""
        pass
    
    async def claim_reward(user_id: uuid.UUID, reward_id: uuid.UUID) -> bool:
        """領取獎勵"""
        pass
```

### 3.2 進度追蹤服務 (ProgressService)

#### 3.2.1 核心方法

```python
class ProgressService:
    """進度追蹤服務 - 使用函數式設計"""
    
    async def get_overall_progress(user_id: uuid.UUID) -> OverallProgress:
        """取得整體學習進度
        
        統計資訊：
        - 總章節數 vs 已完成章節數
        - 總句子數 vs 已練習句子數
        - 累計學習時長
        - 學習天數
        """
        pass
    
    async def get_chapters_progress(user_id: uuid.UUID) -> List[ChapterProgress]:
        """取得所有章節進度"""
        pass
    
    async def get_chapter_detail_progress(
        user_id: uuid.UUID,
        chapter_id: uuid.UUID
    ) -> ChapterDetailProgress:
        """取得特定章節詳細進度"""
        pass
    
    async def calculate_completion_rate(
        user_id: uuid.UUID,
        chapter_id: uuid.UUID
    ) -> float:
        """計算章節完成率"""
        pass
```

#### 3.2.2 統計服務 (StatisticsService)

```python
class StatisticsService:
    """統計服務 - 使用函數式設計"""
    
    async def get_recent_activity_stats(
        user_id: uuid.UUID,
        days: int = 7
    ) -> RecentActivityStats:
        """取得近期活動統計
        
        統計指標：
        - 練習會話數量
        - 錄音句子數量
        - 累計練習時長
        - 平均每日時長
        """
        pass
    
    async def get_learning_statistics(
        user_id: uuid.UUID,
        period: str
    ) -> LearningStatistics:
        """取得學習統計"""
        pass
    
    async def calculate_daily_practice_trend(
        user_id: uuid.UUID,
        days: int = 30
    ) -> List[DailyPracticeData]:
        """計算每日練習趨勢"""
        pass
```

### 3.3 服務間依賴關係

```
CheckinService
├── 依賴 DatabaseService (資料庫操作)
├── 依賴 RewardService (獎勵發放)
└── 依賴 StatisticsService (統計更新)

ProgressService
├── 依賴 DatabaseService (資料庫查詢)
├── 依賴 StatisticsService (進度計算)
└── 使用 PracticeSession、PracticeRecord 資料

StatisticsService
├── 依賴 DatabaseService (資料查詢)
├── 使用 PracticeSession、PracticeRecord 資料
└── 提供快取機制提升效能
```

---

## 4. 資料庫模型規劃

### 4.1 簽到相關模型

#### 4.1.1 每日簽到記錄表 (DailyCheckin)

```python
class DailyCheckin(SQLModel, table=True):
    """每日簽到記錄表"""
    __tablename__ = "daily_checkins"
    
    checkin_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    checkin_date: date = Field(nullable=False)  # 簽到日期（不含時間）
    checkin_time: datetime.datetime = Field(default_factory=datetime.datetime.now)  # 簽到時間
    consecutive_days: int = Field(default=1)  # 簽到時的連續天數
    is_makeup: bool = Field(default=False)  # 是否為補簽
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    
    # 複合唯一索引：一個使用者每日只能簽到一次
    __table_args__ = (UniqueConstraint('user_id', 'checkin_date'),)
    
    # Relationships
    user: "User" = Relationship()
    rewards: List["CheckinReward"] = Relationship(back_populates="checkin")
```

#### 4.1.2 簽到獎勵記錄表 (CheckinReward)

```python
class RewardType(str, Enum):
    POINTS = "points"           # 積分
    BADGE = "badge"            # 徽章
    UNLOCK_CONTENT = "unlock"   # 解鎖內容
    
class CheckinReward(SQLModel, table=True):
    """簽到獎勵記錄表"""
    __tablename__ = "checkin_rewards"
    
    reward_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    checkin_id: uuid.UUID = Field(foreign_key="daily_checkins.checkin_id", nullable=False)
    reward_type: RewardType = Field(nullable=False)
    reward_value: str = Field(nullable=False)  # 獎勵值（積分數量、徽章名稱等）
    reward_amount: int = Field(default=1)  # 獎勵數量
    is_claimed: bool = Field(default=False)  # 是否已領取
    claimed_at: Optional[datetime.datetime] = None  # 領取時間
    expires_at: Optional[datetime.datetime] = None  # 獎勵過期時間
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    
    # Relationships
    user: "User" = Relationship()
    checkin: DailyCheckin = Relationship(back_populates="rewards")
```

#### 4.1.3 使用者簽到統計表 (UserCheckinStats)

```python
class UserCheckinStats(SQLModel, table=True):
    """使用者簽到統計表"""
    __tablename__ = "user_checkin_stats"
    
    stats_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False, unique=True)
    total_checkin_days: int = Field(default=0)  # 總簽到天數
    current_consecutive_days: int = Field(default=0)  # 目前連續簽到天數
    max_consecutive_days: int = Field(default=0)  # 最大連續簽到天數
    last_checkin_date: Optional[date] = None  # 最後簽到日期
    total_points_earned: int = Field(default=0)  # 累計獲得積分
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    
    # Relationships
    user: "User" = Relationship()
```

### 4.2 進度追蹤相關模型

#### 4.2.1 使用者學習統計表 (UserLearningStats)

```python
class UserLearningStats(SQLModel, table=True):
    """使用者學習統計表"""
    __tablename__ = "user_learning_stats"
    
    stats_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False, unique=True)
    
    # 整體統計
    total_practice_sessions: int = Field(default=0)  # 總練習會話數
    completed_practice_sessions: int = Field(default=0)  # 已完成會話數
    total_practice_records: int = Field(default=0)  # 總練習記錄數
    total_practice_duration: int = Field(default=0)  # 總練習時長（秒）
    total_learning_days: int = Field(default=0)  # 總學習天數
    
    # 章節進度統計
    total_chapters: int = Field(default=0)  # 總章節數
    completed_chapters: int = Field(default=0)  # 已完成章節數
    total_sentences: int = Field(default=0)  # 總句子數
    practiced_sentences: int = Field(default=0)  # 已練習句子數
    
    # 時間追蹤
    first_practice_date: Optional[date] = None  # 首次練習日期
    last_practice_date: Optional[date] = None  # 最後練習日期
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    
    # Relationships
    user: "User" = Relationship()
```

#### 4.2.2 章節進度表 (UserChapterProgress)

```python
class UserChapterProgress(SQLModel, table=True):
    """使用者章節進度表"""
    __tablename__ = "user_chapter_progress"
    
    progress_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    chapter_id: uuid.UUID = Field(foreign_key="chapters.chapter_id", nullable=False)
    
    # 進度統計
    total_sentences: int = Field(default=0)  # 該章節總句子數
    practiced_sentences: int = Field(default=0)  # 已練習句子數
    completion_rate: float = Field(default=0.0)  # 完成率 (0.0-1.0)
    
    # 練習統計
    total_practice_sessions: int = Field(default=0)  # 該章節總練習會話數
    completed_practice_sessions: int = Field(default=0)  # 已完成會話數
    total_practice_duration: int = Field(default=0)  # 該章節總練習時長
    
    # 時間追蹤
    first_practice_date: Optional[date] = None  # 首次練習該章節日期
    last_practice_date: Optional[date] = None  # 最後練習該章節日期
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    
    # 複合唯一索引
    __table_args__ = (UniqueConstraint('user_id', 'chapter_id'),)
    
    # Relationships
    user: "User" = Relationship()
    chapter: "Chapter" = Relationship()
```

### 4.3 資料表關係圖

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────────┐
│    Users    │────▷│ DailyCheckins   │────▷│ CheckinRewards   │
│             │     │                 │     │                  │
│  user_id    │     │ user_id (FK)    │     │ checkin_id (FK)  │
│  name       │     │ checkin_date    │     │ reward_type      │
│  role       │     │ consecutive_days│     │ is_claimed       │
└─────────────┘     └─────────────────┘     └──────────────────┘
       │
       │            ┌─────────────────────┐
       └───────────▷│ UserCheckinStats    │
       │            │                     │
       │            │ user_id (FK)        │
       │            │ total_checkin_days  │
       │            │ consecutive_days    │
       │            └─────────────────────┘
       │
       │            ┌─────────────────────┐
       └───────────▷│ UserLearningStats   │
       │            │                     │
       │            │ user_id (FK)        │
       │            │ total_sessions      │
       │            │ completed_chapters  │
       │            └─────────────────────┘
       │
       │            ┌─────────────────────┐     ┌─────────────┐
       └───────────▷│ UserChapterProgress │────▷│  Chapters   │
                    │                     │     │             │
                    │ user_id (FK)        │     │ chapter_id  │
                    │ chapter_id (FK)     │     │ situation_id│
                    │ completion_rate     │     └─────────────┘
                    └─────────────────────┘
```

### 4.4 資料驗證規則

#### 4.4.1 簽到相關驗證
- `checkin_date` 必須為有效日期格式
- `consecutive_days` 必須大於 0
- 同一使用者同一日期只能有一筆簽到記錄
- `reward_amount` 必須大於 0

#### 4.4.2 進度統計相關驗證
- `completion_rate` 必須在 0.0-1.0 之間
- `practiced_sentences` 不能超過 `total_sentences`
- `completed_practice_sessions` 不能超過 `total_practice_sessions`
- 時間欄位必須符合邏輯順序（first_date <= last_date）

---

## 5. 三者關聯與架構設計

### 5.1 系統架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                    │
│  ┌─────────────────┐              ┌─────────────────────┐   │
│  │ CheckinRouter   │              │ ProgressRouter      │   │
│  │                 │              │                     │   │
│  │ /daily         │              │ /overview          │   │
│  │ /status        │              │ /chapters          │   │
│  │ /history       │              │ /recent-activity   │   │
│  │ /rewards       │              │ /statistics        │   │
│  └─────────────────┘              └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   Business Logic Layer                     │
│  ┌─────────────────┐  ┌─────────────────┐ ┌──────────────┐  │
│  │ CheckinService  │  │ ProgressService │ │RewardService │  │
│  │                 │  │                 │ │              │  │
│  │ • daily_checkin │  │ • get_progress  │ │• grant_reward│  │
│  │ • get_status    │  │ • get_chapters  │ │• claim_reward│  │
│  │ • get_history   │  │ • get_activity  │ │• calculate   │  │
│  └─────────────────┘  └─────────────────┘ └──────────────┘  │
│           │                     │                │          │
│           └─────────────────────┼────────────────┘          │
│                                 │                           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              StatisticsService                         │ │
│  │                                                        │ │
│  │ • calculate_stats    • daily_trend                     │ │
│  │ • recent_activity    • learning_metrics                │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     Data Access Layer                      │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                Database Models                          │ │
│  │                                                         │ │
│  │ • DailyCheckin        • UserLearningStats              │ │
│  │ • CheckinReward       • UserChapterProgress            │ │
│  │ • UserCheckinStats    • PracticeSession (existing)     │ │
│  │                       • PracticeRecord (existing)      │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 資料流向分析

#### 5.2.1 簽到流程資料流
```
Client Request → CheckinRouter.daily_checkin()
    ↓
CheckinService.perform_daily_checkin()
    ↓
1. 檢查 DailyCheckin 是否已存在
    ↓
2. 計算連續簽到天數
    ↓
3. 創建 DailyCheckin 記錄
    ↓
4. 更新 UserCheckinStats
    ↓
5. RewardService.calculate_checkin_rewards()
    ↓
6. 創建 CheckinReward 記錄
    ↓
Response to Client
```

#### 5.2.2 進度查詢資料流
```
Client Request → ProgressRouter.get_progress_overview()
    ↓
ProgressService.get_overall_progress()
    ↓
1. 查詢 UserLearningStats
    ↓
2. StatisticsService.get_recent_activity_stats()
    ↓
3. 聚合 PracticeSession 資料
    ↓
4. 聚合 PracticeRecord 資料
    ↓
5. 計算完成率和統計指標
    ↓
Response to Client
```

### 5.3 依賴關係設計

#### 5.3.1 Router 層依賴
```python
# CheckinRouter 依賴
CheckinRouter
├── CheckinService (簽到業務邏輯)
├── RewardService (獎勵系統)
└── Auth Dependency (使用者認證)

# ProgressRouter 依賴
ProgressRouter
├── ProgressService (進度業務邏輯)
├── StatisticsService (統計計算)
└── Auth Dependency (使用者認證)
```

#### 5.3.2 Service 層依賴
```python
# CheckinService 依賴
CheckinService
├── Database Session
├── DailyCheckin Model
├── UserCheckinStats Model
└── RewardService

# ProgressService 依賴
ProgressService
├── Database Session
├── UserLearningStats Model
├── UserChapterProgress Model
├── PracticeSession Model (existing)
├── PracticeRecord Model (existing)
└── StatisticsService

# StatisticsService 依賴
StatisticsService
├── Database Session
├── PracticeSession Model (existing)
├── PracticeRecord Model (existing)
└── Cache Service (optional, for performance)
```

### 5.4 關鍵架構決策

#### 5.4.1 設計模式選擇
- **服務層**：採用函數式設計，避免複雜的狀態管理
- **資料層**：使用 SQLModel 保持與現有架構一致性
- **快取策略**：統計資料使用快取機制提升查詢效能

#### 5.4.2 效能考量
- **統計資料快取**：頻繁查詢的統計資料使用 Redis 快取
- **批次更新**：統計表採用批次更新而非即時更新
- **資料庫索引**：在查詢頻繁的欄位建立索引

#### 5.4.3 擴展性考量
- **獎勵系統**：設計為可擴展的獎勵類型和規則
- **統計指標**：統計服務設計為可輕易新增統計指標
- **多時區支援**：簽到功能考慮使用者時區差異

---

## 6. 實作優先級與里程碑

### 6.1 第一階段 (MVP)
**預計完成時間：2-3 週**

1. **基礎簽到功能**
   - DailyCheckin 模型建立
   - 每日簽到 API
   - 簽到狀態查詢 API

2. **基礎進度追蹤**
   - UserLearningStats 模型建立
   - 整體進度查詢 API
   - 章節進度查詢 API

3. **資料庫遷移**
   - Alembic 遷移檔案
   - 資料庫索引建立

### 6.2 第二階段 (完整功能)
**預計完成時間：2-3 週**

1. **進階簽到功能**
   - 連續簽到天數計算
   - 簽到歷史查詢
   - 基礎獎勵機制

2. **詳細進度統計**
   - 近期活動統計
   - 學習趨勢分析
   - 章節詳細進度

### 6.3 第三階段 (優化與擴展)
**預計完成時間：1-2 週**

1. **效能優化**
   - 快取機制實作
   - 查詢優化
   - 批次處理

2. **進階功能**
   - 進階獎勵系統
   - 成就系統
   - 補簽機制

---

## 7. 風險分析與解決策略

### 7.1 技術風險

#### 7.1.1 效能風險
**風險**：統計查詢可能造成資料庫效能問題
**解決策略**：
- 實作快取機制
- 使用資料庫視圖預計算統計資料
- 實作分頁查詢

#### 7.1.2 資料一致性風險
**風險**：統計資料可能與實際練習資料不一致
**解決策略**：
- 使用資料庫事務確保一致性
- 實作定期資料校驗機制
- 提供資料修復工具

### 7.2 業務風險

#### 7.2.1 使用者體驗風險
**風險**：複雜的獎勵規則可能影響使用者體驗
**解決策略**：
- 採用簡單直觀的獎勵機制
- 提供清楚的獎勵說明
- 實作漸進式功能展示

#### 7.2.2 資料隱私風險
**風險**：進度資料涉及使用者隱私
**解決策略**：
- 實作嚴格的權限控制
- 資料匿名化處理
- 符合資料保護法規

---

## 8. 測試策略

### 8.1 單元測試
- Service 層業務邏輯測試
- 統計計算演算法測試
- 獎勵機制邏輯測試

### 8.2 整合測試
- API 端點測試
- 資料庫操作測試
- 快取機制測試

### 8.3 效能測試
- 大量資料下的查詢效能
- 並發簽到處理能力
- 快取機制有效性

---

## 9. 部署與維運考量

### 9.1 資料庫遷移
- 段階式資料遷移
- 資料備份策略
- 回滾機制

### 9.2 監控與告警
- API 回應時間監控
- 資料庫效能監控
- 簽到異常行為監控

### 9.3 維護工具
- 統計資料修復工具
- 簽到資料匯出工具
- 效能分析工具

---

## 10. 結論

本規劃文件提供了患者端簽到與進度追蹤系統的完整技術架構設計。系統採用模組化設計，確保與現有 VocalBorn 平台的良好整合，同時保持高度的可擴展性和可維護性。

關鍵特色包括：
- 遊戲化的簽到機制提升使用者參與度
- 全面的進度追蹤協助學習管理
- 高效能的統計查詢支援大量資料
- 彈性的獎勵系統滿足不同需求

建議按照三階段實作計畫逐步開發，優先實作核心功能，再逐步擴展進階功能，以確保系統穩定性和使用者體驗。

---

**文件版本**：1.0  
**建立日期**：2025-08-28  
**更新日期**：2025-08-28  
**作者**：系統架構師  
**審核者**：待指定