package dhstest
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.apache.spark.sql.types.{
  IntegerType,
  StringType,
  StructField,
  StructType
}
object Custom {
  val schema = StructType(
    List(
      StructField("id", IntegerType, true),
      StructField("first_name", StringType, true),
      StructField("last_name", StringType, true),
      StructField("email", StringType, true),
      StructField("gender", StringType, true),
      StructField("ip_address", StringType, true)
    )
  )
  def process(dfs: Seq[DataFrame]): DataFrame = {
    //df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING) as value", "1 as groupTest").groupBy("groupTest").count()
    dfs(0).select("first_name", "last_name")
  }
  def sqlProcess(
      spark: SparkSession,
      df: DataFrame,
      topic: String
  ): DataFrame = {
    df.createOrReplaceTempView(topic)
    spark.sql(
      s"SELECT CAST(key AS STRING), CAST(value AS STRING) as value, 1 as groupTest from $topic group by groupTest"
    )
  }
}
