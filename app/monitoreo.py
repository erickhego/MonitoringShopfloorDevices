from flask import Blueprint, render_template, request, Flask, make_response, url_for,redirect, jsonify
import pyodbc
from csv import reader
from typing import Any

app = Flask(__name__)

# bp = Blueprint('monitoreo', __name__, url_prefix = '/')
class db:
    def __init__(self):
        # self.conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=')
        self.conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=#########;DATABASE=#########;UID=#########;PWD=#########')
        self.cursor = self.conn.cursor()
        self.queryDevList = """SELECT DEF_DEVICE.DEVICE_ID FROM DEF_DEVICE ORDER BY DISP_ORDER ASC"""
        self.dictDeviceData: dict = {}

    def executeQuery(self, query: str) -> list:
        '''This funcion executes a query and returns a list with results.'''

        self.cursor.execute(query)
        rows: list = self.cursor.fetchall()
        return rows

    def queryToDict(self, devices) -> dict[str, dict]:
        '''This funcion executes a query to obtain the WI status in the MES and returns a dictionary.
        In the keys it will stores the PC/PL/Printer number, in the values it eill contains all devices specifications.'''

        queryDevStatus = """SELECT DEF_DEVICE.DEVICE_ID,
        DEF_DEVICE.DEVICE_NAME_1,
        T_DEVICE_STATUS.DEVICE_STATUS,
        T_DEVICE_STATUS.DEVICE_STATUS_FACTOR,
        T_WI_DEVICE.WI_NORMAL_SPOOL_NUM,
        T_WI_DEVICE.WI_REISSUE_SPOOL_NUM,
        T_WI_DEVICE.INTERRUPT_STATUS,
        T_WI_LAST_OUTPUT.LAST_OUTPUT_SEQ,
        T_WI_LAST_OUTPUT.UPDATE_TIME
        FROM DEF_DEVICE 
        INNER JOIN T_DEVICE_STATUS ON T_DEVICE_STATUS.DEVICE_ID = DEF_DEVICE.DEVICE_ID
        LEFT JOIN T_WI_DEVICE ON T_WI_DEVICE.DEVICE_ID = DEF_DEVICE.DEVICE_ID
        LEFT JOIN T_WI_LAST_OUTPUT ON (DEF_DEVICE.DEVICE_ID = T_WI_LAST_OUTPUT.DEVICE_ID AND T_WI_LAST_OUTPUT.UPDATE_TIME = ( SELECT MAX(UPDATE_TIME) FROM T_WI_LAST_OUTPUT WHERE DEVICE_ID = DEF_DEVICE.DEVICE_ID))
        WHERE T_DEVICE_STATUS.DEVICE_ID IN (""" + devices + """) ORDER BY DISP_ORDER ASC"""
        rows: list = self.executeQuery(queryDevStatus)
        for row in rows:
            self.dictDeviceData[row.DEVICE_ID] = {}
            self.dictDeviceData[row.DEVICE_ID]['Name'] = row.DEVICE_NAME_1 
            self.dictDeviceData[row.DEVICE_ID]['Status'] = int(row.DEVICE_STATUS)
            self.dictDeviceData[row.DEVICE_ID]['Status_Factor'] = row.DEVICE_STATUS_FACTOR
            self.dictDeviceData[row.DEVICE_ID]['Spool'] = int(row.WI_NORMAL_SPOOL_NUM)
            self.dictDeviceData[row.DEVICE_ID]['Reissue_Spool'] = int(row.WI_REISSUE_SPOOL_NUM)
            self.dictDeviceData[row.DEVICE_ID]['Interrupt_Status'] = int(row.INTERRUPT_STATUS)
            self.dictDeviceData[row.DEVICE_ID]['Last_Seq'] = row.LAST_OUTPUT_SEQ
        return self.dictDeviceData

def csvDataToList(filename: str) -> list[list[str]]:
    '''Read a CSV file and returns a list'''
    # Open the file
    with open(filename) as csvFile:
        # Read csv data
        csvData = reader(csvFile)
        # Store data in a list
        data: list[list[str]] = [data for data in csvData ]
        # Close the csv file
        csvFile.close()
        # Return the data list
        return data

# Displays Smart eye, PLC, and BCR-VPD status. Is the main dashboard of the monitoring
@app.route('/', methods = ['GET', 'POST'])
def index():
    plcData: list[list[str]] = csvDataToList("data/M_PLC.csv")
    smtData: list[list[str]] = csvDataToList("data/M_SMTEYE.csv")
    if request.method == "POST":
        return plcData + smtData
    else:
        return render_template('monitoreo/index.html', plcData = plcData, smtData = smtData)
    
# Opens bcr_status.json (generates from a service) and sends to JS function to be processed.
@app.route('/BCR', methods = ['GET'])
def BCR():
    with open('C:\\inetpub\\wwwroot\\app\\Zebra Monitoreo\\bcr_status.json') as bcr_json:
        bcr_data = bcr_json.read()
    return bcr_data

# Display html template for WI devices connected to MES.
@app.route('/WI_DASHBOARD', methods = ['GET'])
def WI():
    return render_template('monitoreo/WI.html')

# Receives a JSON with selected devices and creates a cookies to save the selections of WI
@app.route('/WI_JSON', methods = ['GET', 'POST'])
def WI_json():
    # Create empty response, after we'll specify more data to this response.
    response = make_response("")

    if request.method == 'POST':
        # Obtain the selected devices
        data: Any = request.json
        # From the json, obtain the data of the key 'selected' 
        selected: list = data.get('selected', [])
        # Transform the data of the list into a entire string to pass it to a cookie
        for_query: str = "'" + "','".join(selected) + "'"
        # In the response add a cookie, with the str of selected devices
        response.set_cookie(key = "wiList", value = for_query, max_age=60*60*24*365)

    elif request.method == 'GET':
        # Ask for a cookie named "wiList", created in the POST method
        try:
            # Request cookie
            cookie: str | None = request.cookies.get("wiList")
            # Data Base instance
            dataBase = db()
            # Execute a query to obtain a dictionary with all selected devices and its characteristics
            dictDevice = dataBase.queryToDict(cookie)
            # Send the dictionary as JSON
            return jsonify(dictDevice)
        except:
            # If a cookie is empty, return an empty dictionary
            emptyDict: dict = {}
            return jsonify(emptyDict)
    
    return response

# Lists all WI devices.
@app.route('/WI_ALL_JSON', methods = ['GET'])
def WI_sel_json():
    # data base instance
    dataBase = db()
    # Obtain data in a list
    rows = dataBase.executeQuery(dataBase.queryDevList)
    # Extract only the number of device
    dev = [i[0] for i in rows]
    # Create an empty dictionary
    dev_dic = {}
    # In key 'Devices' add the full list of devices
    dev_dic['Devices'] = dev
    # Return the dict as JSON
    return jsonify(dev_dic)

# Create a dashboard which contains important IPs
@app.route("/QUICK_LINKS", methods = ["GET", "POST"])
def quickLinks():
    return render_template("monitoreo/links.html")


if __name__ == '__main__':
    app.run(host='0.0.0.0')