'use strict'
// Sets a bounding box around an area in Virginia, USA
const bounds = {
  latMax: 38.735083,
  latMin: 40.898677,
  lngMax: -77.109339,
  lngMin: -81.587841
}

const generateRandomData = (userContext, events, done) => {

  userContext.vars.order_num= Math.random()          //"I'm so happy!"
  return done()
}

module.exports = {
  generateRandomData
}