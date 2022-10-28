const api = require('kucoin-futures-node-api')
const { v4: uuidv4 } = require('uuid')
const fs = require('fs');

const REQUEST_INTERVALS = 105

async function config_and_place_order(
    apiKey,
    secretKey,
    passphrase,
    side,
    symbol,
    type,
    leverage,
    size,
    price
) {
    const config = {
        apiKey: apiKey,
        secretKey: secretKey,
        passphrase: passphrase,
        environment: "live",
    };

    const client = new api();
    client.init(config);

    let res = await place_order(client, side, symbol, type, leverage, size, price);
    // console.log(`${new Date(Date.now())} ${client.apiKey} DONE`);
    return res;
}

async function place_order(
    client,
    side,
    symbol,
    type,
    leverage,
    size,
    price
) {
    params = {
        clientOid: uuidv4(),
        side: side,
        symbol: symbol,
        type: type,
        leverage: leverage,

        size: size,
    };
    if (type == "limit") {
        params.price = price;
    }

    let result = {
        status: "fail",
        retry: false,
        msg: "no msg",

        account: {
            api_key: client.apiKey,
            api_secret: client.secretKey,
            api_passphrase: client.passphrase,
        },

        side: side,
        symbol: symbol,
        size: size,
        price: price,
        leverage: leverage,
        type: type,
    };

    try {
        let r = await client.placeOrder(params);
        result.code = r.code;

        if (r.code == "200000") {
            (result.status = "success"), (result.order_id = r.data.orderId);
        } else {
            result.status = "fail";
            result.msg = r.msg;
        }

        return result;
    } catch (err) {
        if (err.response && err.response.status == 401) {
            result.msg = err.response.data.msg;

            return result;
        } else if (
            (err.response && err.response.status == 429) ||
            err.code == "ECONNRESET" ||
            err.code == "ETIMEDOUT"
        ) {
            result.msg = `Too many request - code: ${
                err.code == undefined ? 429 : err.code
            }`;
        } else {
            result.msg = err.message;

            console.error(err);
        }

        result.retry = true;
        console.log(result.msg);
        return result;
    }
}

async function bulk_config_and_place_order(
    accounts,
    side,
    symbol,
    type,
    leverage,
    size,
    price
) {
    // accounts = Array(2).fill(accounts).flat()
    console.log(`accounts length: ${accounts.length}`);
    let res = [];
    let to_retry_results = [];
    while (true) {
        if (to_retry_results.length > 0) {

            accounts = to_retry_results.map((fail_res) => fail_res.account);
            console.log(`Failed accounts length: ${accounts.length}`);
        }
        const { succeed, failed } = await create_promisees(
            accounts,
            side,
            symbol,
            type,
            leverage,
            size,
            price
        );
        res = res.concat(succeed);
        to_retry_results = failed;
        if (to_retry_results.length == 0) {
            break;
        }
    }

    return res;
}

async function create_promisees(
    accounts,
    side,
    symbol,
    type,
    leverage,
    size,
    price
) {
    let promisees = []
    console.time(`Sent ${accounts.length} request in`);
    for (let index = 0; index < accounts.length; index++) {
        const account = accounts[index];
        let prom = config_and_place_order(
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
        await new Promise(r => setTimeout(r, REQUEST_INTERVALS));
        promisees.push(prom)
    }    

    const chunk_res = await Promise.all(promisees);
    console.timeEnd(`Sent ${accounts.length} request in`);


    const succeed = chunk_res.filter((result) => !result.retry);
    const failed = chunk_res.filter((result) => result.retry);
    console.log(`${failed.length} request failed!`);

    return { succeed, failed };
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

    console.log("writing to file");
    fs.writeFileSync(
        __dirname + "/data/place_order_out.json",
        JSON.stringify(responses),
        "utf-8"
    );
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
