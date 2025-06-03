gcloud dataproc jobs submit pyspark\
  --cluster=spark-cluster\
  --region=europe-west1 \
  --project=taxy-rides-ny-459209 \
  gs://airplanes-bucket-dev/jobs/transformations.py