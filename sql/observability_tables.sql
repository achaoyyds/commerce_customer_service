-- =============================================================
-- 客服系统可观测性（看板）数据表结构
-- 数据库：customer_service（root/123456）
-- 前缀分组：mon_（monitor 埋点/监控）
-- 三张表：dialogue_message（拆历史消息） / dialogue_session（会话） / dialogue_turn（轮次trace）
-- =============================================================

-- 1. 对话消息明细（拆历史：把原来塞在 state_json 里的历史拆成独立行，供看板/审计）
CREATE TABLE IF NOT EXISTS dialogue_message (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    sender_id VARCHAR(64) NOT NULL COMMENT '客户号（customer_no）',
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    turn_id VARCHAR(64) NOT NULL COMMENT '轮次ID',
    message_id VARCHAR(64) NOT NULL COMMENT '消息ID',
    role VARCHAR(16) NOT NULL COMMENT 'user/bot',
    msg_type VARCHAR(16) NOT NULL DEFAULT 'text' COMMENT 'text/object',
    text TEXT NULL COMMENT '消息文本',
    object_id VARCHAR(64) NULL COMMENT '卡片对象ID',
    object_type VARCHAR(32) NULL COMMENT '卡片对象类型',
    object_title VARCHAR(255) NULL COMMENT '卡片对象标题',
    object_attrs JSON NULL COMMENT '卡片对象属性',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_mon_msg_sender (sender_id),
    KEY idx_mon_msg_session (session_id),
    KEY idx_mon_msg_turn (turn_id),
    KEY idx_mon_msg_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话消息明细表（拆历史）';

-- 2. 会话汇总
CREATE TABLE IF NOT EXISTS dialogue_session (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    sender_id VARCHAR(64) NOT NULL COMMENT '客户号',
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    started_at DATETIME NOT NULL COMMENT '开始时间',
    last_active_at DATETIME NOT NULL COMMENT '最近活跃时间',
    closed_at DATETIME NULL COMMENT '结束时间',
    turn_count INT NOT NULL DEFAULT 0 COMMENT '轮次数',
    message_count INT NOT NULL DEFAULT 0 COMMENT '消息数',
    UNIQUE KEY uk_mon_session (session_id),
    KEY idx_mon_session_sender (sender_id),
    KEY idx_mon_session_started (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话会话汇总表';

-- 3. 轮次 trace（执行链路 + 响应耗时 + token 消耗）
CREATE TABLE IF NOT EXISTS dialogue_turn (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    sender_id VARCHAR(64) NOT NULL COMMENT '客户号',
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    turn_id VARCHAR(64) NOT NULL COMMENT '轮次ID',
    message_id VARCHAR(64) NOT NULL COMMENT '本轮 user message_id',
    track VARCHAR(32) NOT NULL COMMENT 'task/knowledge/chitchat/clarify/object',
    flow_id VARCHAR(64) NULL COMMENT '命中流程 code（task 轨道）',
    clarify_reason VARCHAR(64) NULL COMMENT '澄清原因（clarify 轨道）',
    user_text TEXT NULL COMMENT '用户输入',
    bot_text TEXT NULL COMMENT '机器人回复',
    latency_ms INT NOT NULL DEFAULT 0 COMMENT '响应耗时 ms',
    prompt_tokens BIGINT NOT NULL DEFAULT 0 COMMENT '输入 token',
    completion_tokens BIGINT NOT NULL DEFAULT 0 COMMENT '输出 token',
    total_tokens BIGINT NOT NULL DEFAULT 0 COMMENT '总 token',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_mon_turn (turn_id),
    KEY idx_mon_turn_sender (sender_id),
    KEY idx_mon_turn_session (session_id),
    KEY idx_mon_turn_track (track),
    KEY idx_mon_turn_flow (flow_id),
    KEY idx_mon_turn_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话轮次 trace 表';