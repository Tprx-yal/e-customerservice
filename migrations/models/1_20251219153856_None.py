from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `api` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `path` VARCHAR(100) NOT NULL COMMENT 'API路径',
    `method` VARCHAR(6) NOT NULL COMMENT '请求方法',
    `summary` VARCHAR(500) NOT NULL COMMENT '请求简介',
    `tags` VARCHAR(100) NOT NULL COMMENT 'API标签',
    KEY `idx_api_created_78d19f` (`created_at`),
    KEY `idx_api_updated_643c8b` (`updated_at`),
    KEY `idx_api_path_9ed611` (`path`),
    KEY `idx_api_method_a46dfb` (`method`),
    KEY `idx_api_summary_400f73` (`summary`),
    KEY `idx_api_tags_04ae27` (`tags`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `audit_log` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` INT NOT NULL COMMENT '用户ID',
    `username` VARCHAR(64) NOT NULL COMMENT '用户名称' DEFAULT '',
    `module` VARCHAR(64) NOT NULL COMMENT '功能模块' DEFAULT '',
    `summary` VARCHAR(128) NOT NULL COMMENT '请求描述' DEFAULT '',
    `method` VARCHAR(10) NOT NULL COMMENT '请求方法' DEFAULT '',
    `path` VARCHAR(255) NOT NULL COMMENT '请求路径' DEFAULT '',
    `status` INT NOT NULL COMMENT '状态码' DEFAULT -1,
    `response_time` INT NOT NULL COMMENT '响应时间(单位ms)' DEFAULT 0,
    `request_args` JSON COMMENT '请求参数',
    `response_body` JSON COMMENT '返回数据',
    KEY `idx_audit_log_created_277f5d` (`created_at`),
    KEY `idx_audit_log_updated_4bb07a` (`updated_at`),
    KEY `idx_audit_log_user_id_d5b3c4` (`user_id`),
    KEY `idx_audit_log_usernam_b6341e` (`username`),
    KEY `idx_audit_log_module_a9ee07` (`module`),
    KEY `idx_audit_log_summary_88bf13` (`summary`),
    KEY `idx_audit_log_method_2525a0` (`method`),
    KEY `idx_audit_log_path_39c3ce` (`path`),
    KEY `idx_audit_log_status_60fba5` (`status`),
    KEY `idx_audit_log_respons_1e56a2` (`response_time`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `dept` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `name` VARCHAR(20) NOT NULL UNIQUE COMMENT '部门名称',
    `desc` VARCHAR(500) COMMENT '备注',
    `is_deleted` BOOL NOT NULL COMMENT '软删除标记' DEFAULT 0,
    `order` INT NOT NULL COMMENT '排序' DEFAULT 0,
    `parent_id` INT NOT NULL COMMENT '父部门ID' DEFAULT 0,
    KEY `idx_dept_created_4b11cf` (`created_at`),
    KEY `idx_dept_updated_0c0bd1` (`updated_at`),
    KEY `idx_dept_name_c2b9da` (`name`),
    KEY `idx_dept_is_dele_466228` (`is_deleted`),
    KEY `idx_dept_order_ddabe1` (`order`),
    KEY `idx_dept_parent__a71a57` (`parent_id`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `deptclosure` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `ancestor` INT NOT NULL COMMENT '父代',
    `descendant` INT NOT NULL COMMENT '子代',
    `level` INT NOT NULL COMMENT '深度' DEFAULT 0,
    KEY `idx_deptclosure_created_96f6ef` (`created_at`),
    KEY `idx_deptclosure_updated_41fc08` (`updated_at`),
    KEY `idx_deptclosure_ancesto_fbc4ce` (`ancestor`),
    KEY `idx_deptclosure_descend_2ae8b1` (`descendant`),
    KEY `idx_deptclosure_level_ae16b2` (`level`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `file_mapping` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `file_id` VARCHAR(255) NOT NULL UNIQUE COMMENT '文件ID',
    `original_filename` VARCHAR(255) NOT NULL COMMENT '原始文件名',
    `file_type` VARCHAR(50) NOT NULL COMMENT '文件类型',
    `file_size` BIGINT COMMENT '文件大小(字节)',
    `upload_user_id` INT NOT NULL COMMENT '上传用户ID',
    `file_path` VARCHAR(500) COMMENT '本地文件路径',
    KEY `idx_file_mappin_created_519929` (`created_at`),
    KEY `idx_file_mappin_updated_621dab` (`updated_at`),
    KEY `idx_file_mappin_file_id_35e02a` (`file_id`),
    KEY `idx_file_mappin_upload__3562e4` (`upload_user_id`)
) CHARACTER SET utf8mb4 COMMENT='文件映射模型 - 管理文件ID和文件信息的映射关系';
CREATE TABLE IF NOT EXISTS `menu` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `name` VARCHAR(20) NOT NULL COMMENT '菜单名称',
    `remark` JSON COMMENT '保留字段',
    `menu_type` VARCHAR(7) COMMENT '菜单类型',
    `icon` VARCHAR(100) COMMENT '菜单图标',
    `path` VARCHAR(100) NOT NULL COMMENT '菜单路径',
    `order` INT NOT NULL COMMENT '排序' DEFAULT 0,
    `parent_id` INT NOT NULL COMMENT '父菜单ID' DEFAULT 0,
    `is_hidden` BOOL NOT NULL COMMENT '是否隐藏' DEFAULT 0,
    `component` VARCHAR(100) NOT NULL COMMENT '组件',
    `keepalive` BOOL NOT NULL COMMENT '存活' DEFAULT 1,
    `redirect` VARCHAR(100) COMMENT '重定向',
    KEY `idx_menu_created_b6922b` (`created_at`),
    KEY `idx_menu_updated_e6b0a1` (`updated_at`),
    KEY `idx_menu_name_b9b853` (`name`),
    KEY `idx_menu_path_bf95b2` (`path`),
    KEY `idx_menu_order_606068` (`order`),
    KEY `idx_menu_parent__bebd15` (`parent_id`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `role` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `name` VARCHAR(20) NOT NULL UNIQUE COMMENT '角色名称',
    `desc` VARCHAR(500) COMMENT '角色描述',
    KEY `idx_role_created_7f5f71` (`created_at`),
    KEY `idx_role_updated_5dd337` (`updated_at`),
    KEY `idx_role_name_e5618b` (`name`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `user` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `username` VARCHAR(20) NOT NULL UNIQUE COMMENT '用户名称',
    `alias` VARCHAR(30) COMMENT '姓名',
    `email` VARCHAR(255) NOT NULL UNIQUE COMMENT '邮箱',
    `phone` VARCHAR(20) COMMENT '电话',
    `password` VARCHAR(128) COMMENT '密码',
    `is_active` BOOL NOT NULL COMMENT '是否激活' DEFAULT 1,
    `is_superuser` BOOL NOT NULL COMMENT '是否为超级管理员' DEFAULT 0,
    `last_login` DATETIME(6) COMMENT '最后登录时间',
    `dept_id` INT COMMENT '部门ID',
    KEY `idx_user_created_b19d59` (`created_at`),
    KEY `idx_user_updated_dfdb43` (`updated_at`),
    KEY `idx_user_usernam_9987ab` (`username`),
    KEY `idx_user_alias_6f9868` (`alias`),
    KEY `idx_user_email_1b4f1c` (`email`),
    KEY `idx_user_phone_4e3ecc` (`phone`),
    KEY `idx_user_is_acti_83722a` (`is_active`),
    KEY `idx_user_is_supe_b8a218` (`is_superuser`),
    KEY `idx_user_last_lo_af118a` (`last_login`),
    KEY `idx_user_dept_id_d4490b` (`dept_id`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `role_menu` (
    `role_id` BIGINT NOT NULL,
    `menu_id` BIGINT NOT NULL,
    FOREIGN KEY (`role_id`) REFERENCES `role` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`menu_id`) REFERENCES `menu` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_role_menu_role_id_90801c` (`role_id`, `menu_id`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `role_api` (
    `role_id` BIGINT NOT NULL,
    `api_id` BIGINT NOT NULL,
    FOREIGN KEY (`role_id`) REFERENCES `role` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`api_id`) REFERENCES `api` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_role_api_role_id_ba4286` (`role_id`, `api_id`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `user_role` (
    `user_id` BIGINT NOT NULL,
    `role_id` BIGINT NOT NULL,
    FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`role_id`) REFERENCES `role` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_user_role_user_id_d0bad3` (`user_id`, `role_id`)
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "ZA+b3nqA9Rj723rd7v/yHyOqFEg="
)
