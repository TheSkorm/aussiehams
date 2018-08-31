import urllib.request
from io import BytesIO, TextIOWrapper
import zipfile
import csv
import boto3

URL="http://web.acma.gov.au/rrl-updates/spectra_rrl.zip"
SERVICE="6" #based on licence_service.csv
TABLE="australiancallsigns"

db = boto3.client('sdb')


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

def handler(event, context):
    clients={}
    licenses={}
    existing_calls={}
    batch=[]
    with urllib.request.urlopen(URL) as rrl_http:
        with zipfile.ZipFile(BytesIO(rrl_http.read())) as rrl_zip:
            # grab all the client details first so we can look them up
            with rrl_zip.open("client.csv") as clients_file:
                clients_reader = csv.DictReader(TextIOWrapper(clients_file))
                for client in clients_reader:
                    clients[client["CLIENT_NO"]] = client
            with rrl_zip.open("licence.csv") as license_file:
                licenses_reader = csv.DictReader(TextIOWrapper(license_file))
                for licensea in licenses_reader:
                    licenses[licensea["LICENCE_NO"]] = licensea
            with rrl_zip.open("device_details.csv") as device_details:
                device_details_reader = csv.DictReader(TextIOWrapper(device_details))
                for device in device_details_reader:
                    if device['SV_ID'] == SERVICE:
                        try:
                            licensea = licenses[device["LICENCE_NO"]]
                            client = clients[licensea["CLIENT_NO"]]
                        except KeyError:
                            continue
                        key = device['CALL_SIGN']
                        if key == "":
                            continue
                        if key in existing_calls:
                            continue
                        else:
                            existing_calls[key] = True
                        try:
                            batch.append({
                                "Name":key,
                                "Attributes":[
                                    {
                                        "Name": "name",
                                        "Value": client["LICENCEE"],
                                        "Replace": True
                                    },
                                    {
                                        "Name": "suburb",
                                        "Value": client["POSTAL_SUBURB"],
                                        "Replace": True
                                    },
                                    {
                                        "Name": "state",
                                        "Value": client["POSTAL_STATE"],
                                        "Replace": True
                                    },
                                    {
                                        "Name": "type",
                                        "Value": licensea["LICENCE_CATEGORY_NAME"],
                                        "Replace": True
                                    }
                                ]
                            }
                            )
                        except:
                            pass
        dbchunks = list(chunks(batch,25))
        for chunk in dbchunks:
            db.batch_put_attributes(
                DomainName=TABLE,
                Items=chunk
            )
if __name__ == "__main__":
    handler({},{})