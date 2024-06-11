import csv
import asyncio
from io import StringIO

from core.processor_state import State


async def process_file(state: State, filename: str):
    with open(filename, 'rb') as file:
        data = file.read()
        text_data = StringIO(data.decode('utf-8'))
        await process_csv_stream(state, text_data)


async def process_csv_stream(state: State, io: StringIO):
    if not state:
        raise KeyError(f"unable to locate state id {state.id}")

    csv_reader = csv.reader(io)
    header = next(csv_reader)  # Read the header row

    for row in csv_reader:
        # Create a dictionary of key-value pairs for the current row
        query_state = {key: value for key, value in zip(header, row)}

        # apply the query state to the state set
        state.apply_query_state(query_state=query_state)

    return state

async def main():
    state = {
        "state_type": "StateConfig",
        "config": {
            "name": "hello world",
            "version": "version 1.0",
            "storage_class": "memory",
            "primary_key": [
                {"name": "question", "alias": None, "required": True}
            ]
        }
    }
    state = State(**state)
    await process_file(state=state, filename='/Users/kasrarasaee/Downloads/test_questions.csv')


if __name__ == '__main__':
    asyncio.run(main())