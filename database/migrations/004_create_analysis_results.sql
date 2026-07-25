USE datainsight_ai;

CREATE TABLE IF NOT EXISTS analysis_results (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    dataset_id INT UNSIGNED NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    result_json JSON NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_analysis_results_dataset_id (dataset_id),
    CONSTRAINT fk_analysis_results_dataset
        FOREIGN KEY (dataset_id) REFERENCES datasets (id)
        ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
