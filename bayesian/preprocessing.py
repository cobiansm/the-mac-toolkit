import pandas as pd

class Preprocessor:

  def __init__(self, target="Clase"):
    self.target = target
    self.df = None
    self.train = None
    self.test = None

  def load_data(self, file_path):
    # load the csv
    self.df=pd.read_csv(file_path)

  def age_to_bin(self):
    # binning age column
    age_bins = [17, 29, 59, 75];
    age_labels = [0, 1, 2];
    self.df['age-bin'] = pd.cut(self.df['Edad'], bins=age_bins, labels=age_labels, include_lowest=True)

  def income_to_bin(self):
    # binning income column
    income_bins = [9999, 19999, 29999, 39999, 49999, 60000]
    income_labels = [0, 1, 2, 3, 4]
    self.df['income-bin'] = pd.cut(self.df['Ingreso'], bins=income_bins, labels=income_labels, include_lowest=True)

  def train_test_split(self, ratio=0.8):
    # separate train and test df
    total_rows = self.df.shape[0]
    train_size = int(total_rows*ratio)
    self.train = self.df[0:train_size]
    self.test = self.df[train_size:]

  def run(self, file_path, ratio=0.8):
    # run the preprocessing routine
    self.load_data(file_path)
    self.age_to_bin()
    self.income_to_bin()
    self.train_test_split(ratio)
    return self.train, self.test