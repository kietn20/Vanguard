package com.vanguard.guardrail;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;


// Guardrail Service: Safety validation for AI agent actions
@SpringBootApplication
public class GuardrailApplication {

    public static void main(String[] args) {
        SpringApplication.run(GuardrailApplication.class, args);
    }
}
