const api = require('kucoin-futures-node-api')
const { v4: uuidv4 } = require('uuid')
const fs = require('fs');

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

    // console.time(`${client.apiKey} took: `);
    let res = await place_order(client, side, symbol, type, leverage, size, price);
    // console.timeEnd(`${client.apiKey} took: `);
    return res;
}

async function place_order(
    client,
    side,
    symbol,
    type,
    leverage,
    size,
    price,
    retry_count = 0
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
            secret_key: client.secretKey,
            passphrase: client.passphrase,
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

        console.log("success");
        return result;
    } catch (err) {
        if (err.response && err.response.status == 401) {
            result.msg = err.response.data.msg;

            return result;
        } else if (
            (err.response && err.response.status == 429) ||
            err.code == "ECONNRESET"
        ) {
            result.msg = `Too many request - code: ${
                err.code == undefined ? 429 : "ECONNRESET"
            }`;
            console.log(result.msg);
            // await new Promise(r => setTimeout(r, 100));
        } else {
            result.msg = err.message;

            console.error(err);
        }

        // if (retry_count < 10) {
        //     console.log(`${client.apiKey} - Retrying err: ${result.msg}`)
        //     return await place_order(client, side, symbol, type, leverage, size, price, retry_count = retry_count+1)
        // }

        result.retry = true;
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
    // TODO
    accounts = Array(1).fill(accounts).flat();

    console.log(`accounts length: ${accounts.length}`);
    // const chunkSize = 10000;
    let res = [];
    let to_retry_results = [];
    while (true) {
        // for (let i = 0; i < accounts.length; i += chunkSize) {
        //     console.log(`Start: ${i}, End: ${i + chunkSize}`);
        //     const accounts_chunk = accounts.slice(i, i + chunkSize);
        if (to_retry_results.length > 0) {

            console.log(to_retry_results);
            accounts = to_retry_results.map((fail_res) => fail_res.account);
            console.log(`Failed accounts length: ${accounts.length}`);
        }
        const { succeed, failed } = await place_chunk_order(
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

async function place_chunk_order(
    accounts_chunk,
    side,
    symbol,
    type,
    leverage,
    size,
    price
) {
    const promisees = accounts_chunk.map((account) => {
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

    console.log(`Start ${new Date(Date.now())}`);
    console.time(`Sent ${promisees.length} request in`);
    const chunk_res = await Promise.all(promisees);
    console.timeEnd(`Sent ${promisees.length} request in`);

    const succeed = chunk_res.filter((result) => !result.retry);
    const failed = chunk_res.filter((result) => result.retry);
    console.log(`${failed.length} request failed!`);

    await new Promise((r) => setTimeout(r, 15000));
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

    // TODO
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
