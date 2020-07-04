from opcua import Client
from opcua import ua

from opcuaTools import getOpcConnection

import time
import numpy as np
import logging
logging.basicConfig()
#logging.basicConfig(level=logging.DEBUG)

import onnxruntime as onnxrun


# Variable declaration
DINT_Step = 0

OBJ_OpcClient = None
OBJ_OpcNodes = {}

WORD_OpcConfigFilePath = 'opcua_config.json'
WORD_NeuralNetworkModelFilePath = 'model_curvetypes.onnx'


# Input values
REAL_InputVector = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

BOOL_Trigger = False

DINT_JobNumber = 1


# Output values
DINT_ResultVector = 0
# Status
BOOL_Ready = False
BOOL_Error = False
BOOL_DataValid = False

# Runtime Vars
BOOL_EnableLogging = False




while True:

    # === Control structure ===

    if DINT_Step == 0:
        # Initialization

        # Try to connect to OPC UA Client
        logging.info("Connecting to OPC UA Client...")
    
    	# Get connection to OPC server
        OBJ_OpcClient, OBJ_OpcNodes = getOpcConnection(WORD_OpcConfigFilePath)

        # Initialize a few things (set states, loading model into RAM,...)
        try:
            # Set state signal
            OBJ_OpcNodes['BOOL_I_ControllerOn'].set_value(True, ua.VariantType.Boolean)


            # Load NN model into RAM
            print('Starting up Neural Network Runtime...')
            print(' ')

            sess = onnxrun.InferenceSession(WORD_NeuralNetworkModelFilePath)

            print('The model expects input shape: ', sess.get_inputs()[0].shape)

			input_name = sess.get_inputs()[0].name
			label_name = sess.get_outputs()[0].name

			print('Input name: ' + input_name)
			print('Input label name: ' + label_name)
			print(' ')


            BOOL_Error = False
            BOOL_Ready = True

            # Write status values to OPC
            OBJ_OpcNodes['BOOL_I_Ready'].set_value(BOOL_Ready, ua.VariantType.Boolean)
            OBJ_OpcNodes['BOOL_I_Error'].set_value(BOOL_Error, ua.VariantType.Boolean)

            print('All systems go - no errors.')
            print(' ')

            DINT_Step += 10
        except:
            BOOL_Error = True
            BOOL_Ready = False

            # Write status values to OPC
            OBJ_OpcNodes['BOOL_I_Ready'].set_value(BOOL_Ready, ua.VariantType.Boolean)
            OBJ_OpcNodes['BOOL_I_Error'].set_value(BOOL_Error, ua.VariantType.Boolean)

            print('There was an error while starting up.')

            DINT_Step = 99



    elif DINT_Step == 10:
        # Wait for trigger
        BOOL_Trigger = OBJ_OpcNodes['BOOL_IO_Trigger'].get_value()

        if BOOL_Trigger:
            BOOL_Ready = False
            OBJ_OpcNodes['BOOL_I_Ready'].set_value(BOOL_Ready, ua.VariantType.Boolean)
            DINT_Step += 10
        

    elif DINT_Step == 20:
        # Reset trigger signal
        OBJ_OpcNodes['BOOL_IO_Trigger'].set_value(False, ua.VariantType.Boolean)

        # Processing inputs
        print('Started processing...')

        # Get input vector
        REAL_InputVector = OBJ_OpcNodes['REAL_O_InputVector'].get_value()

        print('Input: ')
        print(REAL_InputVector)

        # Feed forward input vector to model

        # Reshape input vector to (1,20)


        # Processing with ONNX Runtime
        start_preprocessing = time.time()
		prediction = np.array(sess.run(None, {input_name: REAL_InputVector}))
		end_preprocessing = time.time()


		pred_conf = prediction[0, 0, np.argmax(prediction)]
		pred_conf = round(pred_conf*100, 2)

		pred_class_index = np.argmax(prediction)




		print('Processing time: ' + str(round((end_preprocessing - start_preprocessing), 3)) + ' ms')

        
        #DINT_ResultVector += 1

        # Write back output to OPC interface
        OBJ_OpcNodes['DINT_I_Result'].set_value(DINT_ResultVector, ua.VariantType.Int32)

        print('Output: ')
        print(DINT_ResultVector)


        # Write status values to OPC
        BOOL_DataValid = True
        BOOL_Ready = True
        OBJ_OpcNodes['BOOL_I_Ready'].set_value(BOOL_Ready, ua.VariantType.Boolean)
        OBJ_OpcNodes['BOOL_IO_DataValid'].set_value(BOOL_DataValid, ua.VariantType.Boolean)


        # Wait for trigger
        DINT_Step = 10


