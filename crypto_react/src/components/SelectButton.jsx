import React from 'react'

const SelectButton = ({children, selected, onClick}) => {
  return (
    <span
    onClick={onClick}
    style={{
            border: "1px solid #6ee755",
            borderRadius: 5,
            padding: 10,
            paddingLeft: 20,
            paddingRight: 20,
            fontFamily: "Montserrat",
            cursor: "pointer",
            backgroundColor: selected ? "#6ee755" : "",
            color: selected ? "black" : "",
            fontWeight: selected ? 700 : 500,
            "&:hover": {
              backgroundColor: "#6ee755",
              color: "#6ee755",
            },
            width: "22%",
    }}>
        {children}
    </span>
  )
}

export default SelectButton
