from typing import Any, Literal

from pydantic import BaseModel, Field


JsonDict = dict[str, Any]


class ImportFileReport(BaseModel):
    processed: list[str] = Field(default_factory=list)
    unsupported: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DetectedHealthSignals(BaseModel):
    heart_rate: bool = False
    steps: bool = False
    sleep: bool = False
    stress: bool = False
    activity: bool = False
    exercise: bool = False
    body_profile: bool = False
    device_profile: bool = False


class AiTwinReadiness(BaseModel):
    score: int = Field(ge=0, le=100)
    level: Literal["low", "medium", "high"]
    reason: str


class DataQuality(BaseModel):
    total_record_count: int = 0
    returned_record_count: int = 0
    samples_truncated: bool = False
    warnings: list[str] = Field(default_factory=list)
    details: JsonDict = Field(default_factory=dict)


class TimeAggregate(BaseModel):
    hour: str | None = None
    date: str | None = None
    avg_bpm: float | None = None
    min_bpm: float | None = None
    max_bpm: float | None = None
    avg_score: float | None = None
    min_score: float | None = None
    max_score: float | None = None
    steps: int | None = None
    distance_meters: float | None = None
    calories: float | None = None
    sample_count: int = 0
    high_bpm_count: int | None = None
    low_bpm_count: int | None = None


class HeartRatePeriod(BaseModel):
    datauuid: str | None = None
    deviceuuid: str | None = None
    package_name: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    avg_bpm: float | None = None
    min_bpm: float | None = None
    max_bpm: float | None = None
    heart_beat_count: int | None = None
    binning_data_ref: str | None = None
    time_offset_ms: int | None = None
    create_time: str | None = None
    update_time: str | None = None
    create_sh_ver: str | None = None
    modify_sh_ver: str | None = None
    client_data_id: str | None = None
    client_data_ver: str | None = None
    comment: str | None = None
    source_file: str
    raw_extra: JsonDict | None = None


class HeartRateSample(BaseModel):
    parent_datauuid: str | None = None
    parent_binning_data_ref: str | None = None
    source_json_file: str
    start_time: str | None = None
    end_time: str | None = None
    duration_seconds: float | None = None
    bpm: float | None = None
    min_bpm: float | None = None
    max_bpm: float | None = None
    raw_extra: JsonDict | None = None


class HeartRateSection(BaseModel):
    detected: bool = False
    summary: JsonDict = Field(default_factory=dict)
    periods: list[HeartRatePeriod] = Field(default_factory=list)
    samples: list[HeartRateSample] = Field(default_factory=list)
    hourly_aggregates: list[TimeAggregate] = Field(default_factory=list)
    daily_aggregates: list[TimeAggregate] = Field(default_factory=list)
    analysis: JsonDict = Field(default_factory=dict)
    data_quality: JsonDict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class StepInterval(BaseModel):
    datauuid: str | None = None
    deviceuuid: str | None = None
    package_name: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    duration_seconds: float | None = None
    steps: int | None = None
    distance_meters: float | None = None
    calories: float | None = None
    speed: float | None = None
    sample_position_type: str | None = None
    time_offset_ms: int | None = None
    create_time: str | None = None
    update_time: str | None = None
    source_file: str
    raw_extra: JsonDict | None = None


class StepDailySummary(BaseModel):
    date: str | None = None
    day_time: str | None = None
    step_count: int | None = None
    walk_step_count: int | None = None
    run_step_count: int | None = None
    healthy_step: int | None = None
    active_time: float | None = None
    distance_meters: float | None = None
    calories: float | None = None
    speed: float | None = None
    achievement: float | None = None
    recommendation: str | None = None
    binning_data_ref: str | None = None
    source_package_name: str | None = None
    package_name: str | None = None
    deviceuuid: str | None = None
    datauuid: str | None = None
    create_time: str | None = None
    update_time: str | None = None
    source_file: str | None = None
    raw_extra: JsonDict | None = None


class StepTrendSample(BaseModel):
    parent_datauuid: str | None = None
    source_json_file: str | None = None
    start_time: str | None = None
    time_unit: str | int | None = None
    steps: int | None = None
    walk_step_count: int | None = None
    run_step_count: int | None = None
    distance_meters: float | None = None
    calories: float | None = None
    speed: float | None = None
    raw_extra: JsonDict | None = None


class StepsSection(BaseModel):
    detected: bool = False
    summary: JsonDict = Field(default_factory=dict)
    intervals: list[StepInterval] = Field(default_factory=list)
    daily_summaries: list[StepDailySummary] = Field(default_factory=list)
    trend_samples: list[StepTrendSample] = Field(default_factory=list)
    recommendations: list[JsonDict] = Field(default_factory=list)
    hourly_aggregates: list[TimeAggregate] = Field(default_factory=list)
    daily_aggregates: list[TimeAggregate] = Field(default_factory=list)
    data_quality: JsonDict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class StressPeriod(BaseModel):
    datauuid: str | None = None
    deviceuuid: str | None = None
    package_name: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    score: float | None = None
    min_score: float | None = None
    max_score: float | None = None
    algorithm: str | None = None
    tag_id: str | None = None
    binning_data_ref: str | None = None
    time_offset_ms: int | None = None
    create_time: str | None = None
    update_time: str | None = None
    comment: str | None = None
    source_file: str | None = None
    raw_extra: JsonDict | None = None


class StressSample(BaseModel):
    parent_datauuid: str | None = None
    source_json_file: str
    start_time: str | None = None
    end_time: str | None = None
    score: float | None = None
    min_score: float | None = None
    max_score: float | None = None
    level: str | int | None = None
    flag: str | int | None = None
    raw_extra: JsonDict | None = None


class StressHistogram(BaseModel):
    datauuid: str | None = None
    deviceuuid: str | None = None
    base_hr: float | None = None
    histogram_ref: str | None = None
    decay_time: str | None = None
    values: list[Any] = Field(default_factory=list)
    version: int | None = None
    source_file: str | None = None
    source_json_file: str | None = None
    raw_extra: JsonDict | None = None


class StressSection(BaseModel):
    detected: bool = False
    summary: JsonDict = Field(default_factory=dict)
    periods: list[StressPeriod] = Field(default_factory=list)
    samples: list[StressSample] = Field(default_factory=list)
    histograms: list[StressHistogram] = Field(default_factory=list)
    hourly_aggregates: list[TimeAggregate] = Field(default_factory=list)
    daily_aggregates: list[TimeAggregate] = Field(default_factory=list)
    data_quality: JsonDict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class ActivityDaySummary(BaseModel):
    date: str | None = None
    day_time: str | None = None
    step_count: int | None = None
    distance_meters: float | None = None
    calories: float | None = None
    active_time: float | None = None
    walk_time: float | None = None
    run_time: float | None = None
    exercise_time: float | None = None
    dynamic_active_time: float | None = None
    longest_active_time: float | None = None
    longest_idle_time: float | None = None
    move_hourly_count: int | None = None
    floor_count: int | None = None
    score: float | None = None
    goal: float | None = None
    target: float | None = None
    movement_type: str | None = None
    energy_type: str | None = None
    extra_data_ref: str | None = None
    deviceuuid: str | None = None
    datauuid: str | None = None
    source_file: str | None = None
    raw_extra: JsonDict | None = None


class ActivityExtraData(BaseModel):
    parent_datauuid: str | None = None
    mMostActiveMinutes: Any = None
    mActivityList: Any = None
    mUnitDataList: Any = None
    mIsGoalAchieved: bool | None = None
    mStreakDayCount: int | None = None
    mAdaptiveGoal: Any = None
    raw_extra: JsonDict | None = None


class ActivityLevelRecord(BaseModel):
    datauuid: str | None = None
    deviceuuid: str | None = None
    package_name: str | None = None
    activity_level: str | int | None = None
    start_time: str | None = None
    time_offset_ms: int | None = None
    create_time: str | None = None
    update_time: str | None = None
    source_file: str | None = None
    raw_extra: JsonDict | None = None


class ActivitySection(BaseModel):
    detected: bool = False
    summary: JsonDict = Field(default_factory=dict)
    day_summaries: list[ActivityDaySummary] = Field(default_factory=list)
    extra_data: list[ActivityExtraData] = Field(default_factory=list)
    activity_levels: list[ActivityLevelRecord] = Field(default_factory=list)
    stand_summaries: list[JsonDict] = Field(default_factory=list)
    goals: list[JsonDict] = Field(default_factory=list)
    data_quality: JsonDict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class ExerciseSession(BaseModel):
    datauuid: str | None = None
    deviceuuid: str | None = None
    package_name: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    duration_seconds: float | None = None
    exercise_type: str | int | None = None
    exercise_custom_type: str | int | None = None
    calories: float | None = None
    distance_meters: float | None = None
    count: float | None = None
    count_type: str | int | None = None
    mean_heart_rate: float | None = None
    min_heart_rate: float | None = None
    max_heart_rate: float | None = None
    mean_speed: float | None = None
    max_speed: float | None = None
    mean_cadence: float | None = None
    max_cadence: float | None = None
    mean_power: float | None = None
    max_power: float | None = None
    vo2_max: float | None = None
    altitude_gain: float | None = None
    altitude_loss: float | None = None
    max_altitude: float | None = None
    min_altitude: float | None = None
    incline_distance: float | None = None
    decline_distance: float | None = None
    sweat_loss: float | None = None
    live_data_ref: str | None = None
    location_data_ref: str | None = None
    additional_ref: str | None = None
    auxiliary_devices: str | None = None
    create_time: str | None = None
    update_time: str | None = None
    source_file: str | None = None
    raw_extra: JsonDict | None = None


class ExerciseLiveSample(BaseModel):
    parent_datauuid: str | None = None
    source_json_file: str
    start_time: str | None = None
    heart_rate: float | None = None
    speed: float | None = None
    distance: float | None = None
    cadence: float | None = None
    raw_extra: JsonDict | None = None


class ExerciseSection(BaseModel):
    detected: bool = False
    summary: JsonDict = Field(default_factory=dict)
    sessions: list[ExerciseSession] = Field(default_factory=list)
    live_samples: list[ExerciseLiveSample] = Field(default_factory=list)
    data_quality: JsonDict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class SleepSession(BaseModel):
    datauuid: str | None = None
    deviceuuid: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    duration_seconds: float | None = None
    sleep_score: float | None = None
    efficiency: float | None = None
    stage: str | int | None = None
    source_file: str | None = None
    raw_extra: JsonDict | None = None


class SleepSection(BaseModel):
    detected: bool = False
    summary: JsonDict = Field(default_factory=lambda: {"session_count": 0})
    sessions: list[SleepSession] = Field(default_factory=list)
    stages: list[JsonDict] = Field(default_factory=list)
    message: str | None = None
    data_quality: JsonDict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class BodyMeasurement(BaseModel):
    type: Literal["height", "weight", "body_composition"]
    start_time: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    body_fat_percent: float | None = None
    body_fat_mass: float | None = None
    skeletal_muscle: float | None = None
    skeletal_muscle_mass: float | None = None
    muscle_mass: float | None = None
    basal_metabolic_rate: float | None = None
    total_body_water: float | None = None
    fat_free: float | None = None
    fat_free_mass: float | None = None
    vfa_level: float | None = None
    deviceuuid: str | None = None
    datauuid: str | None = None
    source_file: str | None = None
    raw_extra: JsonDict | None = None


class UserProfileEntry(BaseModel):
    key: str | None = None
    value: Any = None
    value_type: str | None = None
    deviceuuid: str | None = None
    datauuid: str | None = None
    create_time: str | None = None
    update_time: str | None = None
    source_file: str | None = None
    raw_extra: JsonDict | None = None


class BodyProfileSection(BaseModel):
    detected: bool = False
    summary: JsonDict = Field(default_factory=dict)
    measurements: list[BodyMeasurement] = Field(default_factory=list)
    user_profile: list[UserProfileEntry] = Field(default_factory=list)
    data_quality: JsonDict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class DeviceProfile(BaseModel):
    datauuid: str | None = None
    deviceuuid: str | None = None
    name: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    fixed_name: str | None = None
    device_group: str | None = None
    device_type: str | None = None
    connectivity_type: str | None = None
    accessory_type: str | None = None
    step_source_group: str | None = None
    providing_step_goal: str | None = None
    backsync_step_goal: str | None = None
    capability_ref: str | None = None
    create_time: str | None = None
    update_time: str | None = None
    source_file: str | None = None
    raw_extra: JsonDict | None = None


class DeviceCapability(BaseModel):
    parent_deviceuuid: str | None = None
    parent_datauuid: str | None = None
    protocol_feature: Any = None
    model_name: str | None = None
    wearable_message: Any = None
    wearable_health_version: str | None = None
    receiver: Any = None
    device_type: str | None = None
    config: Any = None
    raw_extra: JsonDict | None = None


class DeviceProfileSection(BaseModel):
    detected: bool = False
    summary: JsonDict = Field(default_factory=dict)
    devices: list[DeviceProfile] = Field(default_factory=list)
    capabilities: list[DeviceCapability] = Field(default_factory=list)
    data_quality: JsonDict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class DailyHealthSummary(BaseModel):
    date: str
    steps: int | None = None
    walking_steps: int | None = None
    running_steps: int | None = None
    distance_meters: float | None = None
    calories: float | None = None
    active_time_seconds: float | None = None
    walk_time_seconds: float | None = None
    run_time_seconds: float | None = None
    exercise_time_seconds: float | None = None
    floor_count: int | None = None
    stand_time: float | None = None
    avg_heart_rate: float | None = None
    min_heart_rate: float | None = None
    max_heart_rate: float | None = None
    heart_rate_sample_count: int | None = None
    high_bpm_count: int | None = None
    low_bpm_count: int | None = None
    stress_avg_score: float | None = None
    stress_min_score: float | None = None
    stress_max_score: float | None = None
    stress_sample_count: int | None = None
    exercise_sessions_count: int | None = None
    exercise_calories: float | None = None
    sleep_minutes: float | None = None
    sleep_score: float | None = None
    data_sources: list[str] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    type: str
    start_time: str | None = None
    end_time: str | None = None
    date: str | None = None
    value: Any = None
    label: str
    source: str
    datauuid: str | None = None
    deviceuuid: str | None = None
    metadata: JsonDict = Field(default_factory=dict)


class SamsungHealthImportResponse(BaseModel):
    source: Literal["samsung_health_export"] = "samsung_health_export"
    import_status: Literal["parsed"] = "parsed"
    ai_twin_ready: bool
    ai_twin_readiness: AiTwinReadiness
    detected: DetectedHealthSignals
    files: ImportFileReport
    heart_rate: HeartRateSection
    steps: StepsSection
    stress: StressSection
    activity: ActivitySection
    exercise: ExerciseSection
    sleep: SleepSection
    body_profile: BodyProfileSection
    device_profile: DeviceProfileSection
    daily_health: list[DailyHealthSummary] = Field(default_factory=list)
    timeline_events: list[TimelineEvent] = Field(default_factory=list)


class SamsungHealthPreviewResponse(BaseModel):
    source: Literal["samsung_health_export"] = "samsung_health_export"
    supported_files: list[str] = Field(default_factory=list)
    unsupported_files: list[str] = Field(default_factory=list)
    counts_by_file_type: dict[str, int] = Field(default_factory=dict)
    record_counts: dict[str, int] = Field(default_factory=dict)
    detected: DetectedHealthSignals
    warnings: list[str] = Field(default_factory=list)
    debug_files: JsonDict | None = None


class SavedRecordCounts(BaseModel):
    counts: dict[str, int] = Field(default_factory=dict)


class DuplicateRecordCounts(BaseModel):
    counts: dict[str, int] = Field(default_factory=dict)


class HealthImportStorageResult(BaseModel):
    import_id: str | None = None
    status: str
    already_imported: bool = False
    message: str | None = None
    existing_import_id: str | None = None
    saved_counts: dict[str, int] = Field(default_factory=dict)
    duplicate_counts: dict[str, int] = Field(default_factory=dict)
    failed_counts: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    affected_dates: list[str] = Field(default_factory=list)
    daily_summaries_updated: int = 0
    ai_twin_profile_updated: bool = False


class SamsungHealthStoredImportResponse(SamsungHealthImportResponse):
    storage: HealthImportStorageResult


class HealthOverviewResponse(BaseModel):
    user_id: str
    latest_import: JsonDict | None = None
    available_data_types: list[str] = Field(default_factory=list)
    date_range: JsonDict = Field(default_factory=dict)
    ai_twin_readiness: JsonDict | None = None
    latest_daily_summary: JsonDict | None = None
    total_records_by_type: dict[str, int] = Field(default_factory=dict)


class DailyHealthSummaryResponse(BaseModel):
    summaries: list[JsonDict] = Field(default_factory=list)


class HeartRateDetailResponse(BaseModel):
    periods: list[JsonDict] = Field(default_factory=list)
    samples: list[JsonDict] = Field(default_factory=list)
    hourly_aggregates: list[JsonDict] = Field(default_factory=list)


class StepDetailResponse(BaseModel):
    intervals: list[JsonDict] = Field(default_factory=list)
    daily_summaries: list[JsonDict] = Field(default_factory=list)
    trend_samples: list[JsonDict] = Field(default_factory=list)
    hourly_aggregates: list[JsonDict] = Field(default_factory=list)


class StressDetailResponse(BaseModel):
    periods: list[JsonDict] = Field(default_factory=list)
    samples: list[JsonDict] = Field(default_factory=list)
    hourly_aggregates: list[JsonDict] = Field(default_factory=list)


class AiTwinHealthContextResponse(BaseModel):
    user_id: str
    user_baseline: JsonDict = Field(default_factory=dict)
    average_steps: float | None = None
    heart_rate_patterns: JsonDict = Field(default_factory=dict)
    stress_patterns: JsonDict = Field(default_factory=dict)
    activity_patterns: JsonDict = Field(default_factory=dict)
    sleep_availability: JsonDict = Field(default_factory=dict)
    missing_data_warnings: list[str] = Field(default_factory=list)
    date_range_used: JsonDict = Field(default_factory=dict)
    confidence: JsonDict = Field(default_factory=dict)


class DailySyncResult(BaseModel):
    status: str
    users_processed: int = 0
    daily_summaries_updated: int = 0
    ai_twin_profiles_updated: int = 0
