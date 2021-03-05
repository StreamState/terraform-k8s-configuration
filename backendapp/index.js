const express = require('express')

const app = express()


app.use(express.urlencoded({ extended: true }))
app.use(express.json())

app.listen(3000, (err) => {
    if (err) throw err
    console.log('Server running in http://127.0.0.1:3000')
})