
class BayesClassifier:

  def __init__(self):
    self.class_priors = {}
    self.joint_probabilities = {}
    self.class_counts = {}
    self.age_bins = [0, 1, 2]
    self.income_bins = [0, 1, 2, 3, 4]
    self.num_combinations = len(self.age_bins) * len(self.income_bins)
    self.alpha = 1

  def fit(self, train_data):
    # calculate P(C)
    self.calculate_priors(train_data)

    # calculate P(x|C)
    self.calculate_joint_probabilities(train_data)

  def calculate_priors(self, train_data):
    # count the registers of each class
    counts = train_data["Clase"].value_counts()

    # save the registers of the classes
    self.class_counts = counts.to_dict()

    # get the total registers in train df
    total = len(train_data)

    # calculate the priori of each class
    for class_name in self.class_counts:
      self.class_priors[class_name] = (self.class_counts[class_name] / total)

  def calculate_joint_probabilities(self, train_data):
    # traverse each class in train df
    for class_name in self.class_counts:

      # filter registers that belong to that class
      class_data = train_data[train_data["Clase"] == class_name]

      # traverse each age and income bin
      for age_bin in self.age_bins:
        for income_bin in self.income_bins:
          # count registers that coincide with age bin and income bin
          count = len(class_data[(class_data["age-bin"] == age_bin)& (class_data["income-bin"] == income_bin)])

          # calculate confitional probability with laplace smoothing
          probability = (count + self.alpha) / (self.class_counts[class_name] + self.alpha * self.num_combinations)

          # save the result with a tuple as a key
          self.joint_probabilities[(age_bin, income_bin, class_name)] = probability

  def evidence(self, age_bin, income_bin):
    evidence_probability = 0

    # sum each class' contribution
    for class_name in self.class_priors:

      # calculate P(x|C)
      conditional_probability = self.joint_probabilities[(age_bin, income_bin, class_name)]

      # calculate P(C)
      prior_probability = self.class_priors[class_name]

      # multiply P(x|C) * P(C)
      evidence_probability += (conditional_probability * prior_probability)

    return evidence_probability

  def posterior(self, age_bin, income_bin, class_name):
    # calculate P(x|C)
    conditional_probability = self.joint_probabilities[(age_bin, income_bin, class_name)]

    # calculate P(C)
    prior_probability = self.class_priors[class_name]

    # calculate P(x)
    evidence_probability = self.evidence(age_bin, income_bin)

    # apply Bayes 
    return (conditional_probability * prior_probability) / evidence_probability

  def predict(self, age_bin, income_bin):
    # calculate posterior probabilities
    prob_caminar = self.posterior(age_bin,income_bin,"Camina")
    prob_conduce = self.posterior(age_bin,income_bin,"Conduce")

    # select the clase with superiori probability 
    if prob_caminar > prob_conduce:
      return "Camina"
    else:
      return "Conduce"

  def predict_proba(self, age_bin, income_bin):
    probabilities = {}

    # calculate the posterior probability of each class
    for class_name in self.class_priors:
      probabilities[class_name] = self.posterior(age_bin, income_bin, class_name)

    return probabilities