package com.crosshub.config.migration;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

@Component
@Order(3)
public class V8TemuCrawlErrorCodeMigration {
    private static final Logger log = LoggerFactory.getLogger(V8TemuCrawlErrorCodeMigration.class);

    private final JdbcTemplate jdbc;

    public V8TemuCrawlErrorCodeMigration(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void migrate() {
        try {
            jdbc.execute("ALTER TABLE temu_crawl_job ADD COLUMN error_code TEXT");
        } catch (Exception ignored) {
            // column may already exist
        }

        jdbc.update("""
                UPDATE temu_crawl_job
                SET error_code = 'CRAWL_INTERRUPTED',
                    error_message = '同步任务已中断，请重新刷新'
                WHERE status = 'failed'
                  AND (error_code IS NULL OR error_code = '')
                  AND error_message = '服务重启中断'
                """);

        jdbc.update("""
                UPDATE temu_crawl_job
                SET error_code = 'CRAWL_NOT_LOGGED_IN',
                    error_message = 'Temu 卖家后台未登录，请先在本机完成登录'
                WHERE status = 'failed'
                  AND (error_code IS NULL OR error_code = '')
                  AND (
                    error_message LIKE '%login%'
                    OR error_message LIKE '%未登录%'
                    OR error_message LIKE '%agentseller%'
                  )
                  AND error_message NOT LIKE '%localStorage%'
                  AND error_message NOT LIKE '%店铺 ID%'
                """);

        jdbc.update("""
                UPDATE temu_crawl_job
                SET error_code = 'CRAWL_MALL_NOT_SELECTED',
                    error_message = 'Temu 卖家后台未选择店铺，请登录后选择店铺'
                WHERE status = 'failed'
                  AND (error_code IS NULL OR error_code = '')
                  AND (
                    error_message LIKE '%localStorage%'
                    OR error_message LIKE '%店铺 ID%'
                    OR error_message LIKE '%mall-info%'
                  )
                """);

        jdbc.update("""
                UPDATE temu_crawl_job
                SET error_code = 'CRAWL_PROCESS_FAILED',
                    error_message = '数据同步失败，请稍后重试'
                WHERE status = 'failed'
                  AND (error_code IS NULL OR error_code = '')
                  AND error_message IS NOT NULL
                  AND error_message != ''
                """);

        log.info("V8 temu crawl error_code migration completed");
    }
}
