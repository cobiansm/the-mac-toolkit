import pandas as pd
import numpy as np

class Evaluator:

  def __init__(self, y_true, y_pred, classes=('Camina','Conduce')):
    self.y_pred = pd.Series(list(y_pred), name="Predicted")
    self.y_true = pd.Series(list(y_true), name="Real")
    self.classes = list(classes)

  def get_confusion_matrix(self):
    #          Predicted
    #          Pos   Neg
    #        +-----+-----+
    #    Pos |  TP |  FN |
    # Actual +-----+-----+
    #    Neg |  FP |  TN |
    #        +-----+-----+
    self.df_confusion = pd.crosstab(self.y_true, self.y_pred)
    self.df_confusion = self.df_confusion.reindex(index=self.classes, columns=self.classes, fill_value=0)
    return self.df_confusion

  def accuracy(self):
    # accuracy = success (diagonal sum) / total
    if self.df_confusion is None:
      self.confusion_matrix()

    return np.diag(self.df_confusion.to_numpy()).sum() / self.df_confusion.to_numpy().sum()

  def report(self):
    # print the confussion matrix and accuracy
    confusion_matrix = self.get_confusion_matrix()
    accuracy = self.accuracy()
    success = int(np.diag(confusion_matrix.to_numpy()).sum())
    total = int(confusion_matrix.to_numpy().sum())
    print("Confusion matrix (rows = real, columns = predicted):")
    print(confusion_matrix)
    print()
    print("Aciertos: {} de {}".format(success, total))
    print("Precisión general: {:.2%}".format(accuracy))