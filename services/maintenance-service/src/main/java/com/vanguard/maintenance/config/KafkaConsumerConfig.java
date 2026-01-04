package com.vanguard.maintenance.config;

import java.util.HashMap;
import java.util.Map;

import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.ConcurrentKafkaListenerContainerFactory;
import org.springframework.kafka.core.ConsumerFactory;
import org.springframework.kafka.core.DefaultKafkaConsumerFactory;
import org.springframework.kafka.support.serializer.JsonDeserializer;

import com.vanguard.maintenance.model.FactoryEvent;


// Kafka Consumer configuration for the Maintenance Service
@Configuration
public class KafkaConsumerConfig {

  @Value("${spring.kafka.bootstrap-servers}")
  private String bootstrapServers;

  @Value("${spring.kafka.consumer.group-id}")
  private String groupId;

  /**
   * Configure the Kafka consumer factory.
   *
   * This creates consumers with specific deserialization settings
   *
   * @return ConsumerFactory configured for FactoryEvent consumption
   */
  @Bean
  public ConsumerFactory<String, FactoryEvent> consumerFactory() {
    Map<String, Object> config = new HashMap<>();

    // Kafka broker connection
    config.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);

    // Consumer group (allows load balancing across multiple instances)
    config.put(ConsumerConfig.GROUP_ID_CONFIG, groupId);

    // Deserializers (convert bytes back to Java objects)
    config.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
    config.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, JsonDeserializer.class);

    // Tell Jackson to trust FactoryEvent class
    config.put(JsonDeserializer.TRUSTED_PACKAGES, "com.vanguard.maintenance.model");

    // Start reading from earliest message if no offset exists
    config.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");

    // Disable auto-commit
    config.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, false);

    return new DefaultKafkaConsumerFactory<>(
        config,
        new StringDeserializer(),
        new JsonDeserializer<>(FactoryEvent.class, false) // false = don't use type headers
    );
  }

  /**
   * Create the listener container factory.
   *
   * This manages the threads that listen to Kafka topics.
   *
   * @return ConcurrentKafkaListenerContainerFactory for handling messages
   */
  @Bean
  public ConcurrentKafkaListenerContainerFactory<String, FactoryEvent> kafkaListenerContainerFactory() {
    ConcurrentKafkaListenerContainerFactory<String, FactoryEvent> factory = new ConcurrentKafkaListenerContainerFactory<>();

    factory.setConsumerFactory(consumerFactory());

    // Number of concurrent consumer threads (start with 1 for simplicity)
    factory.setConcurrency(1);

    return factory;
  }
}
