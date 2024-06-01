import numpy as np

# Generating noise levels from 0 to 70 with a step of 10
noise_levels = np.arange(0, 71, 10)

# Generating accuracies linearly decreasing from 0.99 to around 0.85
start_accuracy = 0.99
end_accuracy = 0.85
accuracies = np.linspace(start_accuracy, end_accuracy, len(noise_levels))

# Pairing noise levels with accuracies
data = np.column_stack((noise_levels, accuracies))

print(data)
