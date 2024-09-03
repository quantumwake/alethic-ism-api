import uuid
from enum import Enum
from typing import Optional, Dict, Union, List
from fastapi import APIRouter
from pydantic import BaseModel
from http_exceptions import check_null_response

from core.processor_state import State

filter_router = APIRouter()

# import restrictedpython


class FilterOperator(Enum):
    EQ = "EQ"
    GT = "GT"
    LT = "LT"


class FilterItem(BaseModel):
    key: str
    operator: Optional[FilterOperator] = FilterOperator.EQ
    value: Union[str, int, bool, float]


class Filter(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    filter_items: Optional[Dict[str, FilterItem]] = None

    def add_filter_item(self, filter_item: FilterItem) -> FilterItem:
        if not self.filter_items:
            self.filter_items = Dict[str, FilterItem] = {}

        self.filter_items[filter_item.key] = filter_item
        return filter_item

    def get_filter_item(self, key) -> Optional[FilterItem]:
        if not self.filter_items or key not in self.filter_items:
            return None

        return self.filter_items[key]

    def apply_filter_on_data(self, data: Union[str, int, bool, float]):
        if not isinstance(data, dict):
            raise NotImplementedError(f'unable to apply filters on none dictionary types, currently not supported')

        # Apply simple filters
        for key, filter_item in self.filter_items.items():
            data_value = data.get(key)
            op = filter_item.operator

            if op == FilterOperator.EQ and data_value != filter_item.value:
                return False
            elif op == FilterOperator.GT and data_value <= filter_item.value:
                return False
            elif op == FilterOperator.LT and data_value >= filter_item.value:
                return False

        # # Apply advanced filter if set
        # if self.advanced_filter:
        #     locals = {"event": event}
        #     try:
        #         result = restrictedpython.eval_restricted(self.advanced_filter, locals)
        #         return bool(result)
        #     except Exception as e:
        #         print(f"Error in advanced filter: {e}")
        #         return False

        return True


class FilterStorage:

    def __init__(self):
        self.filters: Dict[str, Filter] = {}
        # self.advanced_filter = None

    def insert_filter(self, filter: Filter):
        if not self.filters:
            self.filters: Dict[str, Filter] = {}

        if not filter.id:
            filter.id = str(uuid.uuid4())

        self.filters[filter.id] = filter

    def fetch_filter(self, filter_id: str) -> Optional[Filter]:
        return self.filters[filter_id] if filter_id in self.filters else None

    def apply_filter_on_data(self, filter_id: str, data: Union[str, int, bool, float]) -> bool:
        if filter_id not in self.filters:
            return None

        filter = self.filters[filter_id]
        return filter.apply_filter_on_data(data)

    # def apply_filters(self, event):
    #     # Apply simple filters
    #     for key, operator, value in self.simple_filters:
    #         if operator == "eq" and event.get(key) != value:
    #             return False
    #         elif operator == "gt" and event.get(key) <= value:
    #             return False
    #         elif operator == "lt" and event.get(key) >= value:
    #             return False
    #         # Add more operators as needed
    #
    #     # Apply advanced filter if set
    #     if self.advanced_filter:
    #         locals = {"event": event}
    #         try:
    #             result = restrictedpython.eval_restricted(self.advanced_filter, locals)
    #             return bool(result)
    #         except Exception as e:
    #             print(f"Error in advanced filter: {e}")
    #             return False
    #
    #     return True
#
# # Usage example
# filter_system = FilterSystem()
#
# # Simple filters
# filter_system.add_simple_filter("temperature", "gt", 25)
# filter_system.add_simple_filter("status", "eq", "active")
#
# # Advanced filter
# filter_system.set_advanced_filter("""
# if event['temperature'] > 30 and event['humidity'] < 50:
#     return True
# elif event['status'] == 'critical':
#     return True
# return False
# """)
#
# # Test
# test_event = {"temperature": 32, "humidity": 45, "status": "active"}
# result = filter_system.apply_filters(test_event)
# print(f"Event passed filters: {result}")
#


filterStorage = FilterStorage()


@filter_router.get('/{filter_id}')
@check_null_response
async def fetch_filter(filter_id: str) -> Optional[Filter]:
    return filterStorage.fetch_filter(filter_id=filter_id)


@filter_router.post("")
@check_null_response
async def merge_filter(filter: Filter) -> Filter:
    filterStorage.insert_filter(filter)
    return filterStorage.fetch_filter(filter.id)
    # return storage.load_state(state_id=state_id, load_data=load_data)


@check_null_response
@filter_router.put("/apply")
async def apply_filter_on_data(filter_id: str, data: Dict[str, str]) -> bool:
    return filterStorage.apply_filter_on_data(filter_id=filter_id, data=data)


@check_null_response
@filter_router.get("/user/{user_id}")
async def fetch_filters_by_user(user_id: str) -> Optional[List[Filter]]:
    return filterStorage.filters.values()
