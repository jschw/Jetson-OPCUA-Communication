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
DINT_Step = 0

BOOL_EnableLogToCli = True

REAL_StartProcessing = 0.0
REAL_EndProcessing = 0.0

REAL_Prediction = []
REAL_PredictionConfidence = []


def printlog(msg=str):
    if BOOL_EnableLogToCli:
        print(msg)


while True:

    # === Control structure ===

    if DINT_Step == 0:
        # Initialization

        # Try to connect to OPC UA Client
        printlog("Connecting to OPC UA Client...")
    
        # Get connection to OPC server
        OBJ_OpcClient, OBJ_OpcNodes = getOpcConnection(WORD_OpcConfigFilePath)

        # Initialize a few things (set states, loading model into RAM,...)
        try:
            # Set state signal
            OBJ_OpcNodes['BOOL_I_ControllerOn'].set_value(True, ua.VariantType.Boolean)


            # Load NN model into RAM
            printlog('Starting up Neural Network Runtime...')
            printlog(' ')

            sess = onnxrun.InferenceSession(WORD_NeuralNetworkModelFilePath)


            WORD_InputName = sess.get_inputs()[0].name
            WORD_OutputName = sess.get_outputs()[0].name
            WORD_InputShape = str(sess.get_inputs()[0].shape)

            printlog('The model expects input shape: ' + WORD_InputShape)


            printlog('Input name: ' + WORD_InputName)
            printlog('Input label name: ' + WORD_OutputName)
            printlog(' ')


            BOOL_Error = False
            BOOL_Ready = True

            # Write status values to OPC
            OBJ_OpcNodes['BOOL_I_Ready'].set_value(BOOL_Ready, ua.VariantType.Boolean)
            OBJ_OpcNodes['BOOL_I_Error'].set_value(BOOL_Error, ua.VariantType.Boolean)

            printlog('All systems go - no errors.')
            printlog(' ')

            DINT_Step += 10
        except:
            BOOL_Error = True
            BOOL_Ready = False

            # Write status values to OPC
            OBJ_OpcNodes['BOOL_I_Ready'].set_value(BOOL_Ready, ua.VariantType.Boolean)
            OBJ_OpcNodes['BOOL_I_Error'].set_value(BOOL_Error, ua.VariantType.Boolean)

            printlog('There was an error while starting up.')

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

        # Get input vector
        REAL_InputVector = np.array(OBJ_OpcNodes['REAL_O_InputVector'].get_value())
        REAL_InputVector = REAL_InputVector.astype('float32')

        printlog('Input: ')
        printlog(REAL_InputVector)


        # Reshape input vector to (1,20)
        REAL_InputVector = REAL_InputVector.reshape(1, len(REAL_InputVector))
        printlog('Shape: ' + str(REAL_InputVector.shape))


        # Processing with ONNX Runtime
        REAL_StartProcessing = time.time()
        REAL_Prediction = np.array(sess.run(None, {WORD_InputName: REAL_InputVector}))
        REAL_EndProcessing = time.time()


        REAL_PredictionConfidence = REAL_Prediction[0, 0, np.argmax(REAL_Prediction)]
        REAL_PredictionConfidence = round(REAL_PredictionConfidence*100, 2)

        DINT_ResultVector = np.argmax(REAL_Prediction)


        # Write back output to OPC interface
        OBJ_OpcNodes['DINT_I_Result'].set_value(DINT_ResultVector, ua.VariantType.Int32)
        OBJ_OpcNodes['REAL_I_ResultConfidence'].set_value(REAL_PredictionConfidence, ua.VariantType.Float)


        printlog('Output: ')
        printlog(DINT_ResultVector)

        print('Processing time: ' + str(round((REAL_EndProcessing - REAL_StartProcessing), 4)) + ' ms')
        print(' ')


        # Write status values to OPC
        BOOL_DataValid = True
        BOOL_Ready = True
        OBJ_OpcNodes['BOOL_I_Ready'].set_value(BOOL_Ready, ua.VariantType.Boolean)
        OBJ_OpcNodes['BOOL_IO_DataValid'].set_value(BOOL_DataValid, ua.VariantType.Boolean)


        # Wait for trigger
        DINT_Step = 10


