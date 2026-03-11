import React, { createContext, useContext, useEffect, useState } from "react";

const CryptoContext = createContext();

export const CryptoProvider = ({ children }) => {
  const [currency, setCurrency] = useState("GBP");
  const [symbol, setSymbol] = useState("£");

  useEffect(() => {
    if (currency === "GBP") setSymbol("£");
    else if (currency === "USD") setSymbol("$");
  }, [currency]);

  return (
    <CryptoContext.Provider value={{ currency, symbol, setCurrency }}>
      {children}
    </CryptoContext.Provider>
  );
};

export const cryptoState = () => {
  const context = useContext(CryptoContext);

  return context;
};