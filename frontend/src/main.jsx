import React from 'react'
import { createRoot } from 'react-dom/client'
import ConsumableApp from './screens/ConsumableApp'
import './styles.css'

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ConsumableApp />
  </React.StrictMode>
)
