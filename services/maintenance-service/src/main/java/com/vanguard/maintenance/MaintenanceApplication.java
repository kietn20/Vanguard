package com.vanguard.maintenance;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication(exclude = {
    org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration.class,
    org.springframework.boot.autoconfigure.orm.jpa.HibernateJpaAutoConfiguration.class
})
public class MaintenanceApplication {

    public static void main(String[] args) {
        // SpringApplication.run() starts the entire Spring container
        SpringApplication.run(MaintenanceApplication.class, args);
    }
}
