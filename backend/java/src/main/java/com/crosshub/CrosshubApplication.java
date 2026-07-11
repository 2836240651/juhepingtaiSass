package com.crosshub;

import com.crosshub.config.CrawlerProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

@SpringBootApplication
@EnableConfigurationProperties(CrawlerProperties.class)
public class CrosshubApplication {
    public static void main(String[] args) {
        SpringApplication.run(CrosshubApplication.class, args);
    }
}
