const {convertlistByGroup}=require('./index')

describe('convertListByGroup', ()=>{
    test('it returns groups correctly', ()=>{
        const input=[{
            metadata:{
                name:"mytestapp1"
            },
            somekey:"hi"
        },{
            metadata:{
                name:"mytestapp2"
            },
            somekey:"goodbye"
        },{
            metadata:{
                name:"mytestapp1"
            },
            somekey:"hi2"
        }]
        result=convertlistByGroup(input)
        const expected=[
            {
                sparkApp:"mytestapp1",
                value:[
                    {
                        metadata:{
                            name:"mytestapp1"
                        },
                        somekey:"hi"
                    },
                    {
                        metadata:{
                            name:"mytestapp1"
                        },
                        somekey:"hi2"
                    }
                ]
            },
            {
                sparkApp:"mytestapp2",
                value:[
                    {
                        metadata:{
                            name:"mytestapp2"
                        },
                        somekey:"goodbye"
                    }
                ]
            }
        ]
        expect(result).toEqual(expected)
        

    })
})