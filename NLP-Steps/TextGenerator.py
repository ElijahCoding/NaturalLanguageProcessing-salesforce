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

# for input_example_batch, target_example_batch in dataset.take(1):
#     example_batch_predictions = model(input_example_batch)
#     print(example_batch_predictions, '# (batch_size, seq_length, vocab_size)')

model.summary()


def loss(labels, logits):
    return tf.keras.losses.sparse_categorical_crossentropy(labels, logits, from_logits=True)


model.compile(optimizer='adam', loss=loss)

checkpoint_dir = '../training_checkpoints'
# Name of the checkpoint files
checkpoint_prefix = os.path.join(checkpoint_dir, "ckpt_{epoch}")

checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
    filepath=checkpoint_prefix,
    save_weights_only=True)

EPOCHS = 25

history = model.fit(dataset, epochs=EPOCHS, callbacks=[checkpoint_callback])


# tf.train.latest_checkpoint(checkpoint_dir)
# model = build_model(vocab_size, embedding_dim, rnn_units, batch_size=1)
# model.load_weights(tf.train.latest_checkpoint(checkpoint_dir))
# model.build(tf.TensorShape([1, None]))
# model.summary()

def generate_text(model, start_string):
    # Evaluation step (generating text using the learned model)

    # Number of characters to generate
    num_generate = 1000

    # Converting our start string to numbers (vectorizing)
    input_eval = [char2idx[s] for s in start_string]
    input_eval = tf.expand_dims(input_eval, 0)

    # Empty string to store our results
    text_generated = []

    # Low temperatures results in more predictable text.
    # Higher temperatures results in more surprising text.
    # Experiment to find the best setting.
    temperature = 1.0

    # Here batch size == 1
    model.reset_states()
    for i in range(num_generate):
        predictions = model(input_eval)
        # remove the batch dimension
        predictions = tf.squeeze(predictions, 0)

        # using a categorical distribution to predict the character returned by the model
        predictions = predictions / temperature
        predicted_id = tf.random.categorical(predictions, num_samples=1)[-1, 0].numpy()

        # We pass the predicted character as the next input to the model
        # along with the previous hidden state
        input_eval = tf.expand_dims([predicted_id], 0)

        text_generated.append(idx2char[predicted_id])

    return (start_string + ''.join(text_generated))


print(generate_text(model, start_string=u"ROMEO: "))
