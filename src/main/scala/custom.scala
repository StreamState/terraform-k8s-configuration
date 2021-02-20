package dhstest
import org.apache.spark.sql.{DataFrame, SparkSession}
object Custom {
    def process(dfs: Seq[DataFrame]): DataFrame={
        //df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING) as value", "1 as groupTest").groupBy("groupTest").count()
        dfs(0).select("first_name", "last_name")
    }
    def sqlProcess(spark:SparkSession, df: DataFrame, topic: String): DataFrame={
        df.createOrReplaceTempView(topic)
        spark.sql(s"SELECT CAST(key AS STRING), CAST(value AS STRING) as value, 1 as groupTest from $topic group by groupTest")
    }
}