-- =============================================================
-- 运营后台（能力配置中心）数据表结构
-- 数据库：customer_service（客服系统后端已连的库，root/123456）
-- 前缀分组：sys_（账号权限） / kb_（知识库） / cfg_（配置）
-- 说明：金融产品主数据仍在 finance 库，此处只维护客服侧运营资产
-- =============================================================

-- 1. 后台用户（运营/客服/管理员）
CREATE TABLE IF NOT EXISTS sys_user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_no VARCHAR(64) NOT NULL COMMENT '登录账号',
    username VARCHAR(64) NOT NULL,
    password_hash VARCHAR(255) NOT NULL COMMENT 'bcrypt 哈希',
    display_name VARCHAR(64) NOT NULL,
    user_type VARCHAR(16) NOT NULL COMMENT 'admin/operator/agent',
    status VARCHAR(16) NOT NULL DEFAULT 'active' COMMENT 'active/disabled',
    last_login_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_sys_user_no (user_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='运营后台用户表';

-- 2. 知识分类（树形）
CREATE TABLE IF NOT EXISTS kb_category (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    category_code VARCHAR(64) NOT NULL,
    category_name VARCHAR(64) NOT NULL,
    parent_id BIGINT NULL,
    sort_no INT NOT NULL DEFAULT 0,
    yn TINYINT NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_kb_category_code (category_code),
    KEY idx_kb_category_parent (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识分类表';

-- 3. FAQ 条目
CREATE TABLE IF NOT EXISTS kb_faq (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    faq_no VARCHAR(64) NOT NULL,
    category_id BIGINT NOT NULL,
    question VARCHAR(255) NOT NULL,
    answer MEDIUMTEXT NOT NULL,
    keywords JSON NULL COMMENT '检索命中关键词',
    status VARCHAR(16) NOT NULL DEFAULT 'draft' COMMENT 'draft/published/offline',
    sort_no INT NOT NULL DEFAULT 0,
    hit_count BIGINT NOT NULL DEFAULT 0 COMMENT '命中次数，用于排序/反馈',
    created_by BIGINT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_kb_faq_no (faq_no),
    KEY idx_kb_faq_category (category_id),
    KEY idx_kb_faq_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='FAQ 条目表';

-- 4. 流程槽位字典
CREATE TABLE IF NOT EXISTS cfg_slot (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    slot_code VARCHAR(64) NOT NULL COMMENT 'account_no / transaction_date / loan_amount',
    slot_name VARCHAR(64) NOT NULL COMMENT 'label 账户号',
    slot_type VARCHAR(16) NOT NULL DEFAULT 'text' COMMENT 'text/number/date/enum',
    description VARCHAR(255) NOT NULL,
    validate_rule VARCHAR(255) NULL,
    yn TINYINT NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_cfg_slot_code (slot_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='流程槽位字典表';

-- 5. 流程定义
CREATE TABLE IF NOT EXISTS cfg_flow (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    flow_code VARCHAR(64) NOT NULL COMMENT 'account_balance_query / system_cannot_handle',
    flow_name VARCHAR(64) NOT NULL,
    description VARCHAR(255) NOT NULL,
    flow_category VARCHAR(16) NOT NULL DEFAULT 'business' COMMENT 'business/system',
    status VARCHAR(16) NOT NULL DEFAULT 'draft' COMMENT 'draft/published/archived',
    version INT NOT NULL DEFAULT 1,
    created_by BIGINT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_cfg_flow_code_version (flow_code, version),
    KEY idx_cfg_flow_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话流程定义表';

-- 6. 流程步骤（扁平化 collect 的 response/validate）
CREATE TABLE IF NOT EXISTS cfg_flow_step (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    flow_id BIGINT NOT NULL,
    step_code VARCHAR(64) NOT NULL COMMENT 'start / ask_account_no / end',
    step_type VARCHAR(16) NOT NULL COMMENT 'start/end/action/collect',
    sort_no INT NOT NULL DEFAULT 0,
    action_name VARCHAR(64) NULL COMMENT 'action 步',
    args_json JSON NULL COMMENT 'action 步 args（text/mode/prompt）',
    slot_code VARCHAR(64) NULL COMMENT 'collect 步收集的槽位',
    response_mode VARCHAR(16) NULL COMMENT 'static/generate',
    response_text TEXT NULL COMMENT '询问话术',
    response_prompt TEXT NULL COMMENT 'generate 模式拼接',
    validate_condition VARCHAR(255) NULL COMMENT '校验条件表达式',
    validate_fail_text TEXT NULL COMMENT '校验失败话术',
    pos_x DOUBLE NULL COMMENT '画布坐标',
    pos_y DOUBLE NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_cfg_flow_step (flow_id, step_code),
    KEY idx_cfg_flow_step_flow (flow_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='流程步骤表';

-- 7. 步骤连线（static/condition/fallback）
CREATE TABLE IF NOT EXISTS cfg_flow_link (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    flow_id BIGINT NOT NULL,
    from_step_code VARCHAR(64) NOT NULL,
    link_type VARCHAR(16) NOT NULL COMMENT 'static/condition/fallback',
    condition_expr VARCHAR(255) NULL COMMENT 'if 表达式',
    to_step_code VARCHAR(64) NOT NULL,
    sort_no INT NOT NULL DEFAULT 0 COMMENT '多个 next 的求值顺序',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_cfg_flow_link_flow (flow_id),
    KEY idx_cfg_flow_link_from (flow_id, from_step_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='流程步骤连线表';

-- 8. 配置发布快照（支撑热加载与回滚）
CREATE TABLE IF NOT EXISTS cfg_release (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    release_no VARCHAR(64) NOT NULL,
    release_type VARCHAR(16) NOT NULL COMMENT 'flow/intent/faq/knowledge/full',
    target_code VARCHAR(64) NOT NULL COMMENT '目标 flow_code / intent_code / ALL',
    version INT NOT NULL,
    snapshot_json MEDIUMTEXT NOT NULL COMMENT '等价于 FlowList 的序列化，引擎直接反序列化',
    status VARCHAR(16) NOT NULL DEFAULT 'published' COMMENT 'published/rolled_back',
    published_by BIGINT NOT NULL,
    published_at DATETIME NOT NULL,
    remark VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_cfg_release_no (release_no),
    KEY idx_cfg_release_target (release_type, target_code, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='配置发布快照表';