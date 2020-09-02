import os
import tensorflow as tf
import numpy as np

path_to_file = tf.keras.utils.get_file('shakespeare.txt',
                                       'https://storage.googleapis.com/download.tensorflow.org/data/shakespeare.txt')

text = open(path_to_file, 'rb').read().decode(encoding='utf-8')

# print(len(text))

vocab = sorted(set(text))
# print(len(vocab))

char2idx = {u: i for i, u in enumerate(vocab)}
idx2char = np.array(vocab)

text_as_int = np.array([char2idx[char] for char in text])

# print(text_as_int)

# print('{')
# for char, _ in zip(char2idx, range(20)):
#     print('     {:4s}:  {:3d},'.format(repr(char), char2idx[char]))
# print('...\n')
#
# print('{} ----> characters mapped to int ----> {}'.format(repr(text[:13]), text_as_int[:13]))

seq_length = 100
embedding_dim = 256
rnn_units = 1024
# examples_per_epoch = len(text) // (seq_length + 1)

char_dataset = tf.data.Dataset.from_tensor_slices(text_as_int)

# for i in char_dataset.take(5):
#     print(idx2char[i.numpy()])

sequences = char_dataset.batch(seq_length + 1, drop_remainder=True)


# for item in sequences.take(1):
#     print(repr(''.join(idx2char[item.numpy()])))

def split_input_target(chunk):
    input_text = chunk[:-1]
    target_text = chunk[1:]
    return input_text, target_text

dataset = sequences.map(split_input_target)

# for input_example, target_example in dataset.take(1):
#     print('Input data: ', repr(''.join(idx2char[input_example.numpy()])))
#     print('Target data:', repr(''.join(idx2char[target_example.numpy()])))
#
# for i, (input_idx, target_idx) in enumerate(zip(input_example[:5], target_example[:5])):
#     print("Step {:4d}".format(i))
#     print("  input: {} ({:s})".format(input_idx, repr(idx2char[input_idx])))
#     print("  expected output: {} ({:s})".format(target_idx, repr(idx2char[target_idx])))


BATCH_SIZE = 64
BUFFER_SIZE = 10000

dataset = dataset.shuffle(BUFFER_SIZE).batch(BATCH_SIZE, drop_remainder=True)

vocab_size = len(vocab)

def build_model(vocab_size, embedding_dim, rnn_units, batch_size):
    model = tf.keras.Sequential([
        tf.keras.layers.Embedding(vocab_size, embedding_dim, batch_input_shape=[batch_size, None]),
        tf.keras.layers.GRU(rnn_units, return_sequences=True, stateful=True, recurrent_initializer='glorot_uniform'),
        tf.keras.layers.Dense(vocab_size)
    ])
    return model

model = build_model(
    vocab_size=len(vocab),
    embedding_dim=embedding_dim,
    rnn_units=rnn_units,
    batch_size=BATCH_SIZE)

for input_example_batch, target_example_batch in dataset.take(1):
    example_batch_predictions = model(input_example_batch)
    print(example_batch_predictions, '# (batch_size, seq_length, vocab_size)')

model.summary()