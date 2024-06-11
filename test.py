import pickle

from core.base_model import StatusCode
from core.processor_state import (
    State,
    StateConfig,
    StateConfigLM,
    StateConfigDB,
    StateDataColumnDefinition,
    StateDataRowColumnData,
    StateDataColumnIndex,
    StateDataKeyDefinition,
    InstructionTemplate
)

class CustomUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        try:
            return super().find_class(module, name)
        except ModuleNotFoundError as e:

            if 'State' == name:
                return State
            elif 'StateConfig' == name:
                return StateConfig
            elif 'StateConfigLM' == name:
                return StateConfigLM
            elif 'StateConfigDB' == name:
                return StateConfigDB
            elif 'StateDataColumnDefinition' == name:
                return StateDataColumnDefinition
            elif 'StateDataRowColumnData' == name:
                return StateDataRowColumnData
            elif 'StateDataColumnIndex' == name:
                return StateDataColumnIndex
            elif 'StateDataKeyDefinition' == name:
                return StateDataKeyDefinition
            elif 'ProcessorStatus' == name:
                return StatusCode
            elif 'InstructionTemplate' == name:
                return InstructionTemplate

            raise e

test_file = ('/Users/kasrarasaee'
             '/Development/quantumwake/temp_processor_code/states'
             '/animallm/prod/version0_7/p0_eval/'
             '230d7ae5b60054d124a1105b9a76bdf0783efb790c2150a5bcad55a012709295.pickle')


def load_pickle(file_name):
    with open(test_file, 'rb') as f:
        unpickler = CustomUnpickler(f)
        obj = unpickler.load()
        return obj
