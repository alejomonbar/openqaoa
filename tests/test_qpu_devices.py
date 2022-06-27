#   Copyright 2022 Entropica Labs
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import unittest
import json

from openqaoa.devices import DeviceQiskit, DeviceLocal, DeviceAWS, SUPPORTED_LOCAL_SIMULATORS


class TestingDeviceQiskit(unittest.TestCase):

    """These tests check the Object used to access IBMQ and their available
    QPUs can be established.

    For any tests using provided credentials, the tests will only pass if those
    details provided are correct/valid with IBMQ.

    Please ensure that the provided api token, hub, group and project in the 
    crendentials.json are correct.
    All of these can be found in your IBMQ Account Page.
    """

    def setUp(self):

        try:
            opened_f = open('./tests/credentials.json', 'r')
        except FileNotFoundError:
            opened_f = open('credentials.json', 'r')
                
        with opened_f as f:
            json_obj = json.load(f)['QISKIT']
            self.API_TOKEN = json_obj['API_TOKEN']
            self.HUB = json_obj['HUB']
            self.GROUP = json_obj['GROUP']
            self.PROJECT = json_obj['PROJECT']

        if self.API_TOKEN == "YOUR_API_TOKEN_HERE":
            raise ValueError(
                "Please provide an appropriate API TOKEN in crendentials.json.")
        elif self.HUB == "IBMQ_HUB":
            raise ValueError(
                "Please provide an appropriate IBM HUB name in crendentials.json.")
        elif self.GROUP == "IBMQ_GROUP":
            raise ValueError(
                "Please provide an appropriate IBMQ GROUP name in crendentials.json.")
        elif self.PROJECT == "IBMQ_PROJECT":
            raise ValueError(
                "Please provide an appropriate IBMQ Project name in crendentials.json.")

    def test_check_connection_provider_no_backend_wrong_credentials(self):
        
        """
        If no information provided, check_connection should return False.
        The provider_connected attribute should be updated to False.
        """

        device_obj = DeviceQiskit(device_name='', 
                                  api_token='', 
                                  hub='', group='',
                                  project='')

        self.assertEqual(device_obj.check_connection(), False)
        self.assertEqual(device_obj.provider_connected, False)
        self.assertEqual(device_obj.qpu_connected, None)

    def test_check_connection_provider_no_backend_provided_credentials(self):
        
        """
        If no information about the device name, but the credentials
        used are correct, check_connection should return True.
        The provider_connected attribute should be updated to True.
        """

        device_obj = DeviceQiskit(device_name='', 
                                  api_token=self.API_TOKEN,
                                  hub=self.HUB, group=self.GROUP,
                                  project=self.PROJECT)

        self.assertEqual(device_obj.check_connection(), True)
        self.assertEqual(device_obj.provider_connected, True)
        self.assertEqual(device_obj.qpu_connected, None)

    def test_check_connection_provider_right_backend_provided_credentials(self):
        
        """
        If the correct device name is provided and the credentials
        used are correct, check_connection should return True.
        The provider_connected attribute should be updated to True.
        The qpu_connected attribute should be updated to True.
        """

        device_obj = DeviceQiskit(device_name='', 
                                  api_token=self.API_TOKEN,
                                  hub=self.HUB, group=self.GROUP,
                                  project=self.PROJECT)

        device_obj.check_connection()
        valid_qpu_name = device_obj.available_qpus[0]

        device_obj = DeviceQiskit(device_name=valid_qpu_name, 
                                  api_token=self.API_TOKEN, 
                                  hub=self.HUB, group=self.GROUP,
                                  project=self.PROJECT)

        self.assertEqual(device_obj.check_connection(), True)
        self.assertEqual(device_obj.provider_connected, True)
        self.assertEqual(device_obj.qpu_connected, True)

    def test_check_connection_provider_wrong_backend_provided_credentials(self):
        
        """
        If device name provided is incorrect, and not empty, and the credentials
        used are correct, check_connection should return False.
        The provider_connected attribute should be updated to True.
        The qpu_connected attribute should be updated to False.
        """

        device_obj = DeviceQiskit(device_name='random_invalid_backend', 
                                  api_token=self.API_TOKEN,
                                  hub=self.HUB, group=self.GROUP,
                                  project=self.PROJECT)

        self.assertEqual(device_obj.check_connection(), False)
        self.assertEqual(device_obj.provider_connected, True)
        self.assertEqual(device_obj.qpu_connected, False)
        

class TestingDeviceLocal(unittest.TestCase):
    
    """
    This tests check that the Device Object created for local devices have the
    appropriate behaviour.
    """
    
    def test_supported_device_names(self):
        
        for each_device_name in SUPPORTED_LOCAL_SIMULATORS:
            device_obj = DeviceLocal(each_device_name)
            
            self.assertEqual(device_obj.check_connection(), True)
    
    def test_unsupported_device_names(self):
        
        device_obj = DeviceLocal('unsupported_device')
        
        self.assertEqual(device_obj.check_connection(), False)


class TestingDeviceAWS(unittest.TestCase):
    
    """These tests check the Object used to access AWS Braket and their 
    available QPUs can be established.

    For any tests using provided credentials, the tests will only pass if those
    details provided are correct/valid with AWS Braket.

    Please ensure that the provided access keys, aws region and s3 bucket names in the 
    crendentials.json are correct.
    """
    
    def setUp(self):

        try:
            opened_f = open('./tests/credentials.json', 'r')
        except FileNotFoundError:
            opened_f = open('credentials.json', 'r')
                
        with opened_f as f:
            json_obj = json.load(f)['AWS']
            self.AWS_ACCESS_KEY_ID = json_obj['AWS_ACCESS_KEY_ID']
            self.AWS_SECRET_ACCESS_KEY = json_obj['AWS_SECRET_ACCESS_KEY']
            self.AWS_REGION = json_obj['AWS_REGION']
            self.S3_BUCKET_NAME = json_obj['S3_BUCKET_NAME']

        if self.AWS_ACCESS_KEY_ID == "YOUR_ACCESS_KEY_ID":
            raise ValueError(
                "Please provide an appropriate AWS access key ID in crendentials.json.")
        elif self.AWS_SECRET_ACCESS_KEY == "YOUR_SECRET_ACCESS_KEY":
            raise ValueError(
                "Please provide an appropriate AWS secret access key in crendentials.json.")
        elif self.AWS_REGION == "AWS_REGION":
            raise ValueError(
                "Please provide an appropriate AWS region name in crendentials.json.")
        elif self.S3_BUCKET_NAME == "YOUR_S3_BUCKET":
            raise ValueError(
                "Please provide an appropriate S3 bucket name in crendentials.json.")
            
    def test_check_connection_provider_no_backend_wrong_credentials(self):
        
        """
        If no information provided, check_connection should return False.
        The provider_connected attribute should be updated to False.
        """
        
        device_obj = DeviceAWS(device_name = '', aws_access_key_id = '', 
                               aws_secret_access_key = '', aws_region = '', 
                               s3_bucket_name = '')
        
        self.assertEqual(device_obj.check_connection(), False)
        self.assertEqual(device_obj.provider_connected, False)
        self.assertEqual(device_obj.qpu_connected, None)
        
    def test_check_connection_provider_no_backend_provided_credentials(self):
        
        """
        If no information about the device name, but the credentials
        used are correct, check_connection should return True.
        The provider_connected attribute should be updated to True.
        """

        device_obj = DeviceAWS(device_name='', 
                               aws_access_key_id=self.AWS_ACCESS_KEY_ID,
                               aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY, 
                               aws_region=self.AWS_REGION,
                               s3_bucket_name=self.S3_BUCKET_NAME)

        self.assertEqual(device_obj.check_connection(), True)
        self.assertEqual(device_obj.provider_connected, True)
        self.assertEqual(device_obj.qpu_connected, None)

    def test_check_connection_provider_right_backend_provided_credentials(self):
        
        """
        If the correct device name is provided and the credentials
        used are correct, check_connection should return True.
        The provider_connected attribute should be updated to True.
        The qpu_connected attribute should be updated to True.
        """

        device_obj = DeviceAWS(device_name='', 
                               aws_access_key_id=self.AWS_ACCESS_KEY_ID,
                               aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY, 
                               aws_region=self.AWS_REGION,
                               s3_bucket_name=self.S3_BUCKET_NAME)

        device_obj.check_connection()
        valid_qpu_name = device_obj.available_qpus[0]

        device_obj = DeviceAWS(device_name=valid_qpu_name, 
                               aws_access_key_id=self.AWS_ACCESS_KEY_ID,
                               aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY, 
                               aws_region=self.AWS_REGION,
                               s3_bucket_name=self.S3_BUCKET_NAME)

        self.assertEqual(device_obj.check_connection(), True)
        self.assertEqual(device_obj.provider_connected, True)
        self.assertEqual(device_obj.qpu_connected, True)

    def test_check_connection_provider_wrong_backend_provided_credentials(self):
        
        """
        If device name provided is incorrect, and not empty, and the credentials
        used are correct, check_connection should return False.
        The provider_connected attribute should be updated to True.
        The qpu_connected attribute should be updated to False.
        """

        device_obj = DeviceAWS(device_name='random_invalid_backend', 
                               aws_access_key_id=self.AWS_ACCESS_KEY_ID,
                               aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY, 
                               aws_region=self.AWS_REGION,
                               s3_bucket_name=self.S3_BUCKET_NAME)

        self.assertEqual(device_obj.check_connection(), False)
        self.assertEqual(device_obj.provider_connected, True)
        self.assertEqual(device_obj.qpu_connected, False)

if __name__ == '__main__':
    unittest.main()
