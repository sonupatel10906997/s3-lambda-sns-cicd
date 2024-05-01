import json
import boto3
import pandas as pd
import io
import os
from datetime import datetime

def lambda_handler(event, context):
    # TODO implement
    try:
        # print(event)
        
        s3client = boto3.client('s3')
        snsclient = boto3.client('sns')
        
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        print("Source data : {}/{}".format(bucket,key))
        sourcefilekey = "s3//" + bucket + "/" + key

    
        
        response = s3client.get_object(Bucket = bucket, Key = key)
        if response.get("ResponseMetadata",{}).get("HTTPStatusCode",0) == 200:
            print("s3 object successfully retrieved.")
        
        filecontent = response.get("Body").read().decode('utf-8')
        order_df = pd.read_json(io.StringIO(filecontent))
        delivered_df = order_df.loc[order_df['status'] == "delivered"]
        print(delivered_df)
        
        # uploading file to s3 bucket
        TARGET_BUCKET = os.getenv('TARGET_BUCKET')
        jsonObject = delivered_df.to_json(orient='records', indent=4)
        targetkey = datetime.now().strftime('%Y-%m-%d') + "-delivered_orders.json"
        
        s3client.put_object(Body=jsonObject.encode('utf-8'), Bucket=TARGET_BUCKET, Key=targetkey)
        
        #notify sns
        targetfilekey = "s3//" + TARGET_BUCKET +"/" + targetkey
        successmessage = "".join(["Dear Team,  \n", \
                           "raw-filename: %s" %sourcefilekey, \
                              "\nprocessed-filename: %s"%targetfilekey, \
                                "\nmessage: Daily task order completed successfully" ])
        
        
    
        
        TOPIC_ARN = os.getenv('TOPIC_ARN')
        snsclient.publish(TopicArn=TOPIC_ARN, \
                           Message= successmessage, \
                           Subject="Task | process raw orders json | successful" \
                            )
    
    except Exception as err:
        print("Exception Please check!! \n",err)
        errormessage = "".join(["Dear Team,  \n", \
                           "raw-filename: %s" %sourcefilekey, \
                              "\nprocessed-filename: ", \
                                "\nmessage: Excpetion Occurred , Please check the pipeline %s" %err ])
            
        snsclient.publish(TopicArn=TOPIC_ARN, \
                           Message= errormessage, \
                           Subject="Task | process raw orders json | Failed" \
                            )