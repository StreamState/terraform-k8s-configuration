use serde::{Deserialize, Serialize};
//use serde_json::Result;
use std::env;

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct SparkConf {
    #[serde(rename(serialize = "spark.jars.packages"))]
    spark_jars_packages: String,
    #[serde(rename(serialize = "spark.jars.repositories"))]
    spark_jars_repositories: String,
    #[serde(rename(serialize = "spark.jars.ivy"))]
    spark_jars_ivy: String,
    //lets try to use grafana and NOT spark history
    /*#[serde(rename(serialize = "spark.eventLog.enabled"))]
    spark_event_log_enabled: String,
    #[serde(rename(serialize = "spark.eventLog.dir"))]
    spark_event_log_enabled: String,*/
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct HadoopConf {
    #[serde(rename(serialize = "google.cloud.auth.service.account.enable"))]
    google_cloud_auth_service_account_enable: String,
    #[serde(rename(serialize = "google.cloud.auth.service.account.json.keyfile"))]
    google_cloud_auth_service_account_json_keyfile: String,
    #[serde(rename(serialize = "fs.gs.project.id"))]
    fs_gs_project_id: String,
    #[serde(rename(serialize = "fs.gs.system.bucket"))]
    fs_gs_system_bucket: String,
    #[serde(rename(serialize = "fs.gs.impl"))]
    fs_gs_impl: String,
    #[serde(rename(serialize = "fs.AbstractFileSystem.gs.impl"))]
    fs_abstractfilesystem_gs_impl: String,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct RestartPolicy {
    #[serde(rename(serialize = "type"))]
    policy_type: String,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct PrometheusAnnotations {
    #[serde(rename(serialize = "prometheus.io/scrape"))]
    prometheus_io_scrape: String,
    #[serde(rename(serialize = "prometheus.io/path"))]
    prometheus_io_path: String,
    #[serde(rename(serialize = "prometheus.io/port"))]
    prometheus_io_port: String,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct PrometheusMonitoring {
    jmx_exporter_jar: String,
    port: u32,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct CoresMetadata {
    annotations: PrometheusAnnotations,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct Metadata {
    name: String,
    namespace: String,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct Name {
    name: String,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
enum Refs {
    SecretRef(Name),
    ConfigMapRef(Name),
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct SparkCores {
    instances: Option<u32>,
    cores: Option<u32>,
    core_request: Option<String>,
    env_from: Option<Vec<Refs>>,
    memory: String,
    service_account: Option<String>,
    metadata: Option<CoresMetadata>,
    secrets: Vec<Secret>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct Secret {
    name: String,
    path: String,
    secret_type: String,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct Monitoring {
    expose_driver_metrics: bool,
    expose_executor_metrics: bool,
    prometheus: PrometheusMonitoring,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct Spec {
    spark_conf: SparkConf,
    #[serde(rename(serialize = "type"))]
    code_type: String,
    python_version: String,
    mode: String,
    image_pull_policy: String,
    main_application_file: String,
    spark_version: String,
    hadoop_conf: HadoopConf,
    restart_policy: RestartPolicy,
    driver: SparkCores,
    executor: SparkCores,
    image: String,
    arguments: Vec<String>,
    monitoring: Monitoring,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct SparkApplication {
    api_version: String,
    kind: String,
    spec: Spec,
    metadata: Metadata,
}

#[derive(Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
struct Field {
    #[serde(rename(serialize = "type"))]
    field_type: String,
    name: String,
}
#[derive(Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
struct Schema {
    //essentially avro schema
    fields: Vec<Field>,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct TopicAndSchema {
    topic: String,
    schema: Schema,
}

#[derive(Deserialize, Serialize)]
struct MainJobInputs {
    //still need to add kafka info and credentials
    name: String,
    brokers: Vec<String>,
    mode: String,
    schemas: Vec<Schema>,
}

#[derive(Deserialize)]
struct ReplayJobInputs {
    name: String,
    brokers: Vec<String>,
    mode: String,
    max_file_age: String,
    schemas: Vec<Schema>,
}

#[derive(Deserialize)]
enum Input {
    MainJob(MainJobInputs),
    ReplayJob(ReplayJobInputs),
}

//todo, need to loop over main_job.schema to get config per topic
fn convert_main_job_to_struct(
    main_job: &MainJobInputs,
    namespace: String,
    project: String,
    org_bucket: String,
) -> Vec<SparkApplication> {
    vec![SparkApplication {
        api_version: String::from("sparkoperator.k8s.io/v1beta2"),
        kind: String::from("SparkApplication"),
        spec: Spec {
            spark_conf: SparkConf {
                //for these purely static structs I could make more efficient by pre-declaring
                spark_jars_packages: String::from(
                    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.0",
                ),
                spark_jars_repositories: String::from("https://packages.confluent.io/maven"),
                spark_jars_ivy: String::from("/tmp/ivy"),
            },
            code_type: String::from("Python"),
            python_version: String::from("3"),
            mode: String::from("cluster"),
            image_pull_policy: String::from("Always"),
            main_application_file: String::from("local:///opt/spark/work-dir/replay_app.py"),
            spark_version: String::from("3.0.1"),
            hadoop_conf: HadoopConf {
                fs_gs_project_id: project,
                fs_gs_system_bucket: org_bucket,
                google_cloud_auth_service_account_enable: "true".to_string(),
                google_cloud_auth_service_account_json_keyfile: "/mnt/secrets/key.json".to_string(),
                fs_gs_impl: "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem".to_string(),
                fs_abstractfilesystem_gs_impl:
                    "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem".to_string(),
            },
            restart_policy: RestartPolicy {
                policy_type: "Always".to_string(),
            },
            driver: SparkCores {
                core_request: Some("200m".to_string()),
                memory: "512m".to_string(),
                service_account: Some("spark".to_string()), //maps to spark-gcs
                metadata: Some(CoresMetadata {
                    annotations: PrometheusAnnotations {
                        prometheus_io_scrape: "true".to_string(),
                        prometheus_io_path: "/metrics".to_string(),
                        prometheus_io_port: "8090".to_string(),
                    },
                }),
                secrets: vec![Secret {
                    name: "spark-secret".to_string(),
                    path: "/mnt/secrets".to_string(),
                    secret_type: "GCPServiceAccount".to_string(),
                }],
                cores: None,
                instances: None,
                env_from: vec![
                    Refs::SecretRef(Name {
                        name: "cassandra-secret".to_string(),
                    }),
                    Refs::ConfigMapRef(Name {
                        name: "cassandra_and_other_data".to_string(),
                    }),
                ],
            },
            executor: SparkCores {
                instances: Some(1),
                cores: Some(1),
                memory: "512m".to_string(),
                secrets: vec![Secret {
                    name: "spark-secret".to_string(),
                    path: "/mnt/secrets".to_string(),
                    secret_type: "GCPServiceAccount".to_string(),
                }],
                core_request: None,
                metadata: None,
                service_account: None,
                env_from: None,
            },
            monitoring: Monitoring {
                expose_driver_metrics: true,
                expose_executor_metrics: true,
                prometheus: PrometheusMonitoring {
                    jmx_exporter_jar: "/prometheus/jmx_prometheus_javaagent-0.11.0.jar".to_string(),
                    port: 8090,
                },
            },
            ///ohhhh boy...I guess I get this from the previous output in Argo
            image: "helloworld".to_string(),
            arguments: vec![
                main_job.name,
                main_job.brokers.join(","),
                main_job.mode,
                serde_json::to_string(&main_job.schemas).unwrap(),
            ],
        },
        metadata: Metadata {
            name: main_job.name,
            namespace: namespace,
        },
    }]
}

//should have single large JSON object, convert to arguments
//get namespace from config map
fn main() {
    let args: Vec<String> = env::args().collect();
    let namespace = match env::var("spark_namespace") {
        Ok(val) => val,
        Err(_e) => "none".to_string(),
    };
    let project = match env::var("project") {
        Ok(val) => val,
        Err(_e) => "none".to_string(),
    };
    let org_bucket = match env::var("org_bucket") {
        Ok(val) => val,
        Err(_e) => "none".to_string(),
    };
    let input: Input = serde_json::from_str(&args[1]).unwrap();
    match input {
        Input::MainJob(main_job) => {
            convert_main_job_to_struct(&main_job, namespace, project, org_bucket)
        }
        Input::ReplayJob(replay_job) => {}
    }
}
