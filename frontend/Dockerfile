FROM node:latest

WORKDIR /usr/src/

COPY ./finance-dashboard ./finance-dashboard

WORKDIR /usr/src/finance-dashboard

RUN npm install

VOLUME /usr/src/finance-dashboard

CMD ["npm", "start"]