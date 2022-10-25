const api = require('kucoin-futures-node-api')
const { v4: uuidv4 } = require('uuid')
const fs = require('fs');

async function config_and_place_order(apiKey, secretKey, passphrase, side, symbol, type, leverage, size, price){
    const config = {
        apiKey: apiKey,
        secretKey: secretKey,
        passphrase: passphrase,
        environment: 'live'
    }

    const client = new api()
    client.init(config)

    return await place_order(client, side, symbol, type, leverage, size, price)
}

async function place_order(client, side, symbol, type, leverage, size, price, fail_count=0) {
    params = {
        clientOid: uuidv4(),
        side: side,
        symbol: symbol,
        type: type,
        leverage: leverage,

        size: size,
    }
    if (type == "limit") {
        params.price = price
    }
    result = {
        "api_key": client.apiKey,
        "status": "fail",
        "side": side,
        "symbol": symbol,
        "size": size,
        "price": price,
        "leverage": leverage,
        "type": type,
    }
    try {
        let r = await client.placeOrder(params)
        result.code = r.code

        if (r.code == "200000") {
            result.status = "success",
            result.order_id = r.data.orderId
        }
        else {
            result.status = "fail"
            result.msg = r.msg
        }

        console.log(result);        
        return result
    } catch (err) {
        if (err.response && err.response.status == 401) {
            result.msg = err.response.data.msg

            return result
        } else if (err.response && err.response.status == 429) {
            result.msg = "Too many request"

            await new Promise(r => setTimeout(r, 1000));
        } else {
            result.msg = err.message

            console.error(err)
            // console.log(`${err.response.statusText} : ${err.response.data.code} - ${err.response.data.msg}`)
        }

        if (fail_count < 10) {
            console.log(`${client.apiKey} - Retrying err: ${result.msg}`)
            // console.log(`${client.apiKey.substring(5, 8)} - Retrying err: ${result.msg}`)
            return await place_order(client, side, symbol, type, leverage, size, price, fail_count = fail_count+1)
        }

        return result
    }    
}

async function bulk_config_and_place_order(accounts, side, symbol, type, leverage, size, price) {
    promisees = accounts.map(account => {
        console.log(account)
        return config_and_place_order(
            account.api_key,
            account.api_secret,
            account.api_passphrase,
            side,
            symbol,
            type,
            leverage,
            size,
            price
        );
    });
    console.time(`Sent ${promisees.length} request in`)
    res = await Promise.all(promisees)
    console.log(`\n`)
    console.timeEnd(`Sent ${promisees.length} request in`)
    console.log(`\n`)
    return res
}

async function read_from_file_place_order() {
    let raw_data = fs.readFileSync(__dirname+"/data/place_order_in.json");
    let data = JSON.parse(raw_data);

    responses = await bulk_config_and_place_order(
        data.accounts,
        data.side,
        data.symbol,
        data.type,
        data.leverage,
        data.size,
        data.price,
    )

    fs.writeFileSync(__dirname+"/data/place_order_out.json", JSON.stringify(responses), "utf-8")
}

read_from_file_place_order()
    
// bulk_config_and_place_order(
//     accounts = [{
//         apiKey: "633e67428209b100012a4ece",
//         secretKey: "40adac37-4cda-4dfe-bdc4-fa3bce439fd8",
//         passphrase: "dtNe6tF6Sy4PtXV"
//     }],
//     side = "buy",
//     symbol = "XBTUSDTM",
//     type = "limit",
//     leverage = "5",
//     size = 1,
//     price = "100000"
// ) 
