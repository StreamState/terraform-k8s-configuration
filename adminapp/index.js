const fastify = require('fastify')()
const path = require('path')
fastify.register(require('fastify-static'), {
    root: path.join(__dirname, 'public'),
    prefix: '/public/', // optional: default '/'
})
fastify.register(require('fastify-formbody'))
const {
    CONFLUENT_KEY_NAME: confluentKeyName,
    CONFLUENT_SECRET_NAME: confluentSecretName
} = process.env



fastify.listen(process.env.PORT, '0.0.0.0').then((address) => {
    console.log(`Server running at ${address}`);
})
fastify.get('/', (req, reply) => {
    return reply.sendFile('hello.html') // serving path.join(__dirname, 'public', 'myHtml.html') directly
})

