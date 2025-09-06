import pickle


def unsafe_deserialize(serialized_data):
    return pickle.loads(serialized_data)
