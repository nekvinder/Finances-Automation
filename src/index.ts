// const slackOAuthToken = getEnv('SLACK_OAUTH_TOKEN');
require('dotenv').config();
// const discordToken = getEnv('DISCORD_TOKEN');
// const discordClientID = getEnv('DISCORD_CLIENT_ID');
const database_id = getEnv('NOTION_DB_ID');
//imports
// const { WebClient } = require('@slack/web-api');
import { tempdata } from './test';
const date = require('date-and-time');
const fs = require('fs');
const { Client } = require('@notionhq/client');

// Initializing
// const web = new WebClient(slackOAuthToken);
const notion = new Client({ auth: getEnv('NOTION_SECRET') });

export async function getDBData(isTest = true) {
  if (isTest) {
    return tempdata;
  }
  const myPage = await notion.databases.query({ database_id });
  return myPage.results.map((val) => val.properties);
}

async function getCsvDataFromNotion(isTest = false) {
  const res = await getDBData(isTest);
  const data = res
    .map((v) => {
      if (v.Date.date && v.Date.date.start) {
        (v as any).Date = date.format(
          new Date(v.Date.date.start),
          'DD/MM/YYYY'
        );
        (v as any)['Category-Select'] = v['Category-Select'].select.name;
        (v as any)['Amount'] = v['Amount'].number;
        (v as any)['Name'] = v['Name'].title[0].plain_text;
        return v;
      } else {
        console.log('Invalid entry', v, v.Date);
        return null;
      }
    })
    .filter((v) => v);

  await fs.writeFileSync('data.json', JSON.stringify(data));
  const { Parser } = require('json2csv');

  try {
    const parser = new Parser();
    const csv = parser.parse(data);
    await fs.writeFileSync('data.csv', csv);
  } catch (err) {
    console.error(err);
  }
}

export async function makeChartsPy(): Promise<void> {
  const execSync = require('child_process').execSync;
  const result = execSync('python3 main.py');
  console.log(result.toString('utf8'));
}

async function main() {
  // const slackThread = await sendSlack('Started expenses analysis');
  await getCsvDataFromNotion();
  //   await makeChartsPy();
  const files = fs.readdirSync('images');
  const uris = [];
  for (const file of files) {
    const filePath = `./images/${file}`;
    console.log(filePath);
    // uris.push(await uploadImagesAndGetURIs(filePath));
    break;
  }
  console.log(uris);

  //   const { REST, Routes } = require('discord.js');

  //   const commands = [
  //     {
  //       name: 'ping',
  //       description: 'Replies with Pong!',
  //     },
  //   ];

  //   const rest = new REST({ version: '10' }).setToken(discordToken);

  //   (async () => {
  //     try {
  //       console.log('Started refreshing application (/) commands.');

  //       await rest.put(Routes.applicationCommands(discordClientID), {
  //         body: commands,
  //       });

  //       console.log('Successfully reloaded application (/) commands.');
  //     } catch (error) {
  //       console.error(error);
  //     }
  //   })();

  //   const { Client, GatewayIntentBits } = require('discord.js');
  //   const client = new Client({ intents: [GatewayIntentBits.Guilds] });

  //   client.on('ready', () => {
  //     console.log(`Logged in as ${client.user.tag}!`);
  //   });

  //   client.on('interactionCreate', async (interaction) => {
  //     if (!interaction.isChatInputCommand()) return;

  //     if (interaction.commandName === 'ping') {
  //       await interaction.reply('Pong!');
  //     }
  //   });

  //   client.login(discordToken);
}

main();

function getEnv(key: string) {
  const value = process.env[key];
  if (value === undefined) {
    throw new Error(`Environment variable ${key} is not defined`);
  }
  return value;
}

// async function sendSlack(msg: string, slackThread?: string) {
//   const result = await web.chat.postMessage({
//     text: msg,
//     channel: 'general',
//     thread_ts: slackThread ?? '',
//   });
//   console.log(result);
//   return result.ts;
// }
