
def calculate_metrics(data):
    '''Calculate various metrics from data.'''
    return sum(data) / len(data)

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def process_data(self, input_data):
        return [x * 2 for x in input_data]
