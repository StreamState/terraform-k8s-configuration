FROM node:16-alpine3.13
WORKDIR /usr/app
ADD index.js index.js
ADD utils.js utils.js
ADD package.json package.json  
ADD package-lock.json package-lock.json 
ADD public public
RUN npm ci
CMD ["node", "index.js"]
