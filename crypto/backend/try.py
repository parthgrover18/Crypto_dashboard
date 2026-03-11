import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
import pandas_ta as ta

data = yf.download("BTC-USD", period="max", interval="1d", auto_adjust=False)

data.columns = data.columns.droplevel(1)

data['RSI'] = ta.rsi(data['Close'], length=15)
data['EMAF'] = ta.ema(data['Close'], length=20)
data['EMAM'] = ta.ema(data['Close'], length=100)
data['EMAS'] = ta.ema(data['Close'], length=150)


data['Target'] = data['Adj Close']-data.Open
data['Target'] = data['Target'].shift(-1)

target_class_values = []

for i in range(len(data)):
    if data['Target'][i] > 0:
        target_class_values.append(1)
    else:
        target_class_values.append(0)

data['TargetClass'] = target_class_values


data['TargetNextClose'] = data['Adj Close'].shift(-1)

data.dropna(inplace=True)

data.reset_index(inplace=True)
data.drop(['Volume', 'Close', 'Date'], axis=1, inplace=True)

data.to_csv('btc.txt', index=False)
print(data)


data_set = data.iloc[:, 0:11]
pd.set_option('display.max_columns', None)



# #print(data_set.shape)
# #print(data.shape)
# #print(type(data_set))
# #Target column Categories
# #y =[1 if data.Open[i]>data.Close[i] else 0 for i in range(0, len(data))]
# #yi = [data.Open[i]-data.Close[i] for i in range(0, len(data))]
# #print(yi)
# #print(len(yi))



from sklearn.preprocessing import MinMaxScaler
sc = MinMaxScaler(feature_range=(0,1))
data_set_scaled = sc.fit_transform(data_set)
print(data_set_scaled)















# multiple feature from data provided to the model
X = []
#print(data_set_scaled[0].size)
#data_set_scaled=data_set.values
backcandles = 30
print(data_set_scaled.shape[0])
for j in range(8):#data_set_scaled[0].size):#2 columns are target not X
    X.append([])
    for i in range(backcandles, data_set_scaled.shape[0]):#backcandles+2
        X[j].append(data_set_scaled[i-backcandles:i, j])

#move axis from 0 to position 2
X=np.moveaxis(X, [0], [2])

#Erase first elements of y because of backcandles to match X length
#del(yi[0:backcandles])
#X, yi = np.array(X), np.array(yi)
# Choose -1 for last column, classification else -2...
X, yi =np.array(X), np.array(data_set_scaled[backcandles:,-1])
y=np.reshape(yi,(len(yi),1))
#y=sc.fit_transform(yi)
#X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))
print(X)
print(X.shape)
print(y)
print(y.shape)
#also comprehensions for X
#X = np.array([data_set_scaled[i-backcandles:i,:4].copy() for i in range(backcandles,len(data_set_scaled))])
#print(X)
#print(X.shape)
# split data into train test sets
splitlimit = int(len(X)*0.8)
print(splitlimit)
X_train, X_test = X[:splitlimit], X[splitlimit:]
y_train, y_test = y[:splitlimit], y[splitlimit:]
print(X_train.shape)
print(X_test.shape)
print(y_train.shape)
print(y_test.shape)
print(y_train)

from keras.layers import LSTM
from keras.layers import Dense

import tensorflow as tf
import keras
from keras import optimizers
from keras.models import Model
from keras.layers import Dense, Dropout, LSTM, Input, Activation, concatenate
import numpy as np
#tf.random.set_seed(20)
np.random.seed(10)

lstm_input = Input(shape=(backcandles, 8), name='lstm_input')
inputs = LSTM(150, name='first_layer')(lstm_input)
inputs = Dense(1, name='dense_layer')(inputs)
output = Activation('linear', name='output')(inputs)
model = Model(inputs=lstm_input, outputs=output)
adam = optimizers.Adam()
model.compile(optimizer=adam, loss='mse')
model.fit(x=X_train, y=y_train, batch_size=15, epochs=30, shuffle=True, validation_split = 0.1)
y_pred = model.predict(X_test)
#y_pred=np.where(y_pred > 0.43, 1,0)
for i in range(10):
    print(y_pred[i], y_test[i])
plt.figure(figsize=(16,8))
plt.plot(y_test, color = 'black', label = 'Test')
plt.plot(y_pred, color = 'green', label = 'pred')
plt.legend()
plt.show()





