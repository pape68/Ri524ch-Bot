import discord
import asyncio 
import requests 
import json 
import motor 
from motor.motor_asyncio import AsyncIOMotorClient 
from discord.ext import commands
from discord.commands import Option
import random
import string
import time 


from discord import Intents


intents = discord.Intents.all()


bot = discord.Bot(Intents=intents)

TOKEN = ''

@bot.event
async def on_ready():
    activity = discord.Game(name="/login")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print("Bot is online!")


class Emoji:
    DENY = "<a:deny:1066326613014364160>"
    CHECKMARK = "<a:checkmark:1066327424536686663>"
    WINDOWS = "<:windows:1072644001661976656>"
    LOADING = "<a:loading:1125550892859527309>"
    WARN = "<:warning:1126156805106565190>"

class Color:
    BLUE = 0x44a8fa
    RED  = 0xfa4459
    YELLOW = 0xe8c800



DATABASE_CLUSTER = AsyncIOMotorClient("")
db = DATABASE_CLUSTER["Gorb0"]
user_data = db["USER_DATA"]

import aiohttp


###################################################### UTILS

async def FetchAvatarUser(user_id):
    Account_Check = await user_data.find_one({"UserId": user_id})

    token_ref = Account_Check['AccessToken']
    accountid = Account_Check['AccountId']

    headers = {"Authorization": f"Bearer {token_ref}"}
    url = f"https://avatar-service-prod.identity.live.on.epicgames.com/v1/avatar/fortnite/ids?accountIds={accountid}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            idavatar = data[0]['avatarId']
            idavatar = idavatar.replace('ATHENACHARACTER:', '')

            return f"https://fortnite-api.com/images/cosmetics/br/{idavatar}/icon.png"

async def UpdateInfoAccount(user_id):
    Account_Check = await user_data.find_one({"UserId": user_id})

    accountid = Account_Check['AccountId']
    deviceId = Account_Check['DeviceId']
    secret = Account_Check['Secret']

    session = aiohttp.ClientSession()

    async with session.post("https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token", data=f"grant_type=device_auth&account_id={accountid}&device_id={deviceId}&secret={secret}",headers={'Content-Type': 'application/x-www-form-urlencoded','Authorization': f'basic MzQ0NmNkNzI2OTRjNGE0NDg1ZDgxYjc3YWRiYjIxNDE6OTIwOWQ0YTVlMjVhNDU3ZmI5YjA3NDg5ZDMxM2I0MWE='}) as r:
        if r.status == 200:
            data = await r.json()
            access_code, display_name, account_id = data['access_token'], data['displayName'], data['account_id']

            DataInsert = {
                    "UserId": user_id, 
                    "AccessToken": access_code, 
                    "AccountId": account_id, 
                    "DisplayName": display_name,
                    "DeviceId": deviceId, 
                    "Secret": secret
                }

            await user_data.update_one({"UserId": user_id}, {"$set": DataInsert})                
            await session.close()

def convert_seconds(seconds):
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return minutes, remaining_seconds

################################################################################################################################



#Embed Error(s)

UnknownError = discord.Embed(title=f"`❌ Authorization Error ❌`",description="New authorization code needed. Logout and log back in with a new auth.",colour= discord.Colour.brand_red())    
NotLoggedIn = discord.Embed(description="**`❌ Not Logged In, Try /login ❌`**",colour=discord.Colour.brand_red())
YouCannotDoThis = discord.Embed(title= "`❌ Access Denied ❌`", description= "You cannot do this command here for an unspecified reason.",colour=discord.Colour.brand_red())
YouAreNotWhitelisted = discord.Embed(title= "`❌ Access Denied ❌`", description= "**You Are not Whitelisted.**",colour=discord.Colour.brand_red())

#Reload 

@bot.slash_command(name = "reload", description = "Reloads all  commands.")
async def reload(ctx):
    if ctx.author.id == 909577125256921098:
        embed1 = discord.Embed(title="Reloading...", color=0x0091ff)
        embed2 = discord.Embed(title="Reloaded!", color=0x0091ff)
        embed3 = discord.Embed(title=f"<a:yes:1082644643944091718> Reload complete, {bot.user}!", color=0x0091ff)
        await ctx.respond(embed=embed1)
        bot.reload_extension
        embed2 = discord.Embed(title=f"Reloaded!", color=0x0091ff)
        await ctx.edit(embed=embed2)
        await ctx.edit(embed=embed3)

    else:
        await ctx.respond("You are not a dev.", ephemeral=True)

#Login 

class Login(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="Authorization Code."))


    async def callback(self, interaction: discord.Interaction):
        Data_Check = await user_data.find_one({"UserId": interaction.user.id})
        if Data_Check is None:
            try:

                HeaderData = {
                    "Content-Type": f"application/x-www-form-urlencoded",
                    "Authorization": f"basic MzQ0NmNkNzI2OTRjNGE0NDg1ZDgxYjc3YWRiYjIxNDE6OTIwOWQ0YTVlMjVhNDU3ZmI5YjA3NDg5ZDMxM2I0MWE="
                }
                LoginData = f"grant_type=authorization_code&code={self.children[0].value}"
                LoginRequest = requests.post("https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token",headers=HeaderData,data=LoginData)

                display_name = LoginRequest.json()['displayName']
                accountId = LoginRequest.json()['account_id']
                access_code = LoginRequest.json()['access_token']

                headers = {'Authorization': f'Bearer {access_code}'}
                response = requests.post(url=f'https://account-public-service-prod.ol.epicgames.com/account/api/public/account/{accountId}/deviceAuth', headers=headers)
                device_id, secret = response.json()['deviceId'], response.json()['secret']


                DataInsert = {
                    "UserId": interaction.user.id, 
                    "AccessToken": access_code, 
                    "AccountId": accountId, 
                    "DisplayName": display_name,
                    "DeviceId": device_id, 
                    "Secret": secret
                }

                await user_data.insert_one(DataInsert)

                avatar = await FetchAvatarUser(interaction.user.id)



                embed = discord.Embed(
                    title=f"You are now logged in as, `{display_name}`",
                    description="You have been added to our databases",
                    colour= discord.Colour.brand_green()
                )
                embed.set_thumbnail(url=avatar)


                await interaction.response.send_message(embeds=[embed])

            except:
                await interaction.respond.send_message("Authorization Code Expired.")

        else:
            embed = discord.Embed(title="Logged In Already",description=f"You are already logged in as, `{Data_Check['DisplayName']}`",colour=discord.Colour.green())
            await interaction.response.send_message(embeds=[embed]) 



class LoginGUI(discord.ui.View):  # Create a class called MyView that subclasses discord.ui.View

    @discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
    async def button_callback(self, button, interaction: discord.Interaction):
        modal = Login(title="Authorization Code")
        await interaction.response.send_modal(modal)

@bot.slash_command(description="Login to your fortnite account.")
@commands.cooldown(1, 60, commands.BucketType.user)
async def login(ctx):
    GUI = LoginGUI()
    Add_Component = GUI.add_item(discord.ui.Button(label="Authorization Code", style=discord.ButtonStyle.link, url="https://www.epicgames.com/id/api/redirect?clientId=3446cd72694c4a4485d81b77adbb2141&responseType=code"))
    embed = discord.Embed(
        title="**`Login Process.`**",
        description="To login follow these steps to login :\n\n`1.` Click The Button Named Authorization Code\n\n`2.` Copy Your Authorization Code\n\n`3.` Paste Your Authorization Code in Submit\n\nWrong Account or authorizationCode shows null try [this](https://www.epicgames.com/id/login?redirectUrl=https%3A%2F%2Fwww.epicgames.com%2Fid%2Fapi%2Fredirect%3FclientId%3D3446cd72694c4a4485d81b77adbb2141%26responseType%3Dcode)",
        colour = discord.Colour.brand_green(),
    )
    await ctx.respond(embed=embed, view=GUI)






#Logout Command



@bot.slash_command(description="Log out of your fortnite account.")
@commands.cooldown(1, 60, commands.BucketType.user)
async def logout(ctx):
    Data_Check = await user_data.find_one({"UserId": ctx.author.id})
    if Data_Check is None:
        await ctx.respond(embed=NotLoggedIn)
    else:

        await user_data.delete_one({"UserId": ctx.author.id})
        embed = discord.Embed(title="Logged Out.",description=f"You are now logged out!",colour=discord.Colour.green())
        await ctx.respond(embed=embed)





@bot.slash_command(description="Leaves the party.")
@commands.cooldown(1, 60, commands.BucketType.user)
async def leave(ctx):
    await ctx.defer()

    Account_Check = await user_data.find_one({"UserId": ctx.author.id})

    if Account_Check is None:
        await ctx.respond(embed=NotLoggedIn)
    else:
        token_ref = Account_Check['AccessToken']
        accountid = Account_Check['AccountId'] 

        display_name = Account_Check['DisplayName']

        avatar = await FetchAvatarUser(ctx.author.id)    

        headers = {"Authorization": f"Bearer {token_ref}"}
        url = f"https://party-service-prod.ol.epicgames.com/party/api/v1/Fortnite/user/{accountid}"
        response = requests.get(url, headers=headers)

        party = response.json()['current']

        if party == []:
            embed = discord.Embed(title="Error", description="You are not in a party.", color=discord.Color.red())
            await ctx.respond(embed=embed)
        else:
            party_id = party[0]['id']

            url = f"https://party-service-prod.ol.epicgames.com/party/api/v1/Fortnite/parties/{party_id}/members/{accountid}"
            response = requests.delete(url, headers=headers)

            left = discord.Embed(title="Successfully Left!", colour=discord.Colour.green())
            left.set_thumbnail(url=avatar)
            await ctx.respond(embed=left)

            await ctx.response.send_message(embeds=[left], ephemeral=True)








@bot.slash_command(name="ghost-equip", description="Ghost equip")
@commands.cooldown(1, 60, commands.BucketType.user)
async def ghostequip(ctx, skin: discord.Option(str, description="Skin", required=True)):

    await ctx.defer()
    account_Check = await user_data.find_one({"UserId": ctx.author.id})

    if account_Check is None:
        await ctx.respond(embed=NotLoggedIn)

    else:
        await UpdateInfoAccount(ctx.author.id)

        token_ref = account_Check['AccessToken']
        accountid = account_Check['AccountId'] 
        display_name = account_Check['DisplayName']

        url = f'https://fortnite-api.com/v2/cosmetics/br/search?name={skin}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:

                    embed = discord.Embed(description=f'The {skin} skin does not exist try again!', color=discord.Color.red())
                    embed.set_author(name=display_name, icon_url=ctx.author.avatar)
                    await ctx.respond(embed=embed)

                else:

                    data = await response.json()
                    id_item = data['data']['id']
                    name_item = data['data']['name']

                    headers = {
                        "Authorization": f"Bearer {token_ref}"
                    }
                    url = f"https://party-service-prod.ol.epicgames.com/party/api/v1/Fortnite/user/{accountid}"

                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:

                                data = await response.json()
                                currrent = data['current']

                                if currrent == []:
                                    embed = discord.Embed(description='You are not in a game.', color=discord.Color.red())
                                    embed.set_author(name=display_name, icon_url=ctx.author.avatar)
                                    await ctx.respond(embed=embed)

                                else:
                                    partyId = data['current'][0]['id']

                                    data = {
                                        "Default:AthenaCosmeticLoadout_j": json.dumps({
                                        "AthenaCosmeticLoadout": {
                                        "characterDef": f"/Game/Athena/Items/Cosmetics/Characters/{id_item}.{id_item}"
                                    }})}


                                    body = {
                                        'delete': [],
                                        'revision': 1,
                                        'update': data
                                    }

                                    url = f"https://party-service-prod.ol.epicgames.com/party/api/v1/Fortnite/parties/{partyId}/members/{accountid}/meta"

                                    try:

                                        response = requests.patch(url=url, headers=headers, json=body)
                                        if response.status_code == 200:
                                            embed = discord.Embed(title="Ghost Equip", description=f"Succesfully equipped **{name_item}**", color=discord.Color.green())
                                            embed.set_thumbnail(url=f'https://fortnite-api.com/images/cosmetics/br/{name_item}/icon.png')
                                            await ctx.respond(embed=embed)
                                        else: 

                                            titolo = response.json()['errorCode']
                                            if titolo == 'errors.com.epicgames.social.party.stale_revision':

                                                mexvars = response.json()['messageVars']
                                                revision = max(mexvars)

                                                body = {
                                                    'delete': [],
                                                    'revision': revision,
                                                    'update': data
                                                }

                                                url = f"https://party-service-prod.ol.epicgames.com/party/api/v1/Fortnite/parties/{partyId}/members/{accountid}/meta"
                                                response = requests.patch(url=url, headers=headers, json=body)
                                                embed = discord.Embed(title="Ghost Equip", description=f"Succesfully equipped **{name_item}**", color=discord.Color.green())
                                                embed.set_thumbnail(url=f'https://fortnite-api.com/images/cosmetics/br/{id_item}/icon.png')

                                                await ctx.respond(embed=embed)

                                    except requests.exceptions.JSONDecodeError:

                                        embed = discord.Embed(title="Ghost Equip", description=f"Succesfully equipped **{name_item}**", color=discord.Color.green())
                                        embed.set_thumbnail(url=f'https://fortnite-api.com/images/cosmetics/br/{id_item}/icon.png')
                                        await ctx.respond(embed=embed)





#Friends menu

class Panel2(discord.ui.View):  

    @discord.ui.button(label="Clear All", style=discord.ButtonStyle.primary)
    async def button_callback2(self, button, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        Account_Check = await user_data.find_one({"UserId": interaction.user.id})
        await UpdateInfoAccount(interaction.user.id)

        token_ref = Account_Check['AccessToken']
        accountid = Account_Check['AccountId']
        display_name = Account_Check['DisplayName']

        avatar = await FetchAvatarUser(interaction.user.id)

        headers = {
            "Authorization": f"Bearer {token_ref}"
        }
        requests.delete(f"https://friends-public-service-prod.ol.epicgames.com/friends/api/v1/{accountid}/friends", headers=headers)


        cembed = discord.Embed(
                title="Successful!",
                description=f"Cleared All Friends of {display_name}",
                colour=discord.Color.green()
        )
        await interaction.followup.send(embeds=[cembed])
        cembed.set_thumbnail(url=avatar)


    @discord.ui.button(label="Unblock All", style=discord.ButtonStyle.primary)
    async def button_callback3(self, button, interaction: discord.Interaction):
        Account_Check = await user_data.find_one({"UserId": interaction.user.id})
        await UpdateInfoAccount(interaction.user.id)


        token_ref = Account_Check['AccessToken']
        accountid = Account_Check['AccountId']
        display_name = Account_Check['DisplayName']

        avatar = await FetchAvatarUser(interaction.user.id)

        headers = {
            "Authorization": f"Bearer {token_ref}"
        }
        deletereq = requests.delete(f"https://friends-public-service-prod.ol.epicgames.com/friends/api/public/blocklist/{accountid}", headers=headers)

        bembed = discord.Embed(
                title="Successful!",
                description=f"Unblocked All Blocked Users from {display_name}!",
                colour=discord.Color.green()
        )
        await interaction.response.send_message(embeds=[bembed], ephemeral=True)
        bembed.set_thumbnail(url=avatar)



@bot.slash_command(description="Displays the friends menu.")
@commands.cooldown(1, 60, commands.BucketType.user)
async def friends(ctx):
    await ctx.defer()

    Account_Check = await user_data.find_one({"UserId": ctx.author.id})

    if Account_Check is None:
        await ctx.respond(embed=NotLoggedIn)
    else:
        GUI = Panel2()
        embed = discord.Embed(
            title="Friends List",
            description="Click Whichever Button You Want to Do Certain Actions on the Account Logged in!\n\n[Join Our Support Server For Help](https://discord.gg/ri524ch)",
            colour=discord.Colour.blue(),
        )
        await ctx.respond(embed=embed, view=GUI, ephemeral=False)        



from dateutil import parser


@bot.slash_command(name="account-info",description="Displays current account and account info.")
@commands.cooldown(1, 60, commands.BucketType.user)
async def info(ctx):
    await ctx.defer()

    auth = await user_data.find_one({"UserId": ctx.author.id})

    if auth is None:
        embed = discord.Embed(title=f"Failed", description="You are not logged into the bot!\nTo log in, run the /login")
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar)
        embed.set_footer(text="Bot by Ri524ch")
        await ctx.respond(embed=embed)

    else:
        await UpdateInfoAccount(ctx.author.id)

        accountId = auth['AccountId']
        accessToken = auth['AccessToken']

        url = f"https://account-public-service-prod.ol.epicgames.com/account/api/public/account/{accountId}"
        headers = {
            "Authorization": f"Bearer {accessToken}"
        }

        response = requests.get(url, headers=headers)

        data = response.json()

        accountId = data['id']
        displayName = data['displayName']
        email = data['email']
        country = data['country']
        tfaEnabled = data['tfaEnabled']
        failedLoginAttempts = data['failedLoginAttempts']
        emailVerified = data['emailVerified']
        canUpdateDisplayName = data['canUpdateDisplayName']
        lastDisplayNameChange = data['lastDisplayNameChange']
        numberOfDisplayNameChanges = data['numberOfDisplayNameChanges']
        lastLogin = data['lastLogin']
        preferredLanguage = data['preferredLanguage']


        lastDisplayNameChange = parser.parse(lastDisplayNameChange).strftime("%Y-%m-%d %H:%M:%S")
        lastLogin = parser.parse(lastLogin).strftime("%Y-%m-%d %H:%M:%S")

        embed = discord.Embed(color=Color.YELLOW)
        embed.add_field(name="Account Externals:", value=f">>> :id: `{accountId}`\n`{displayName}`", inline=True)
        embed.add_field(name="Email:", value=f"> {email} {Emoji.CHECKMARK if emailVerified == True else Emoji.DENY}", inline=False)
        embed.add_field(name="Display Name:", value=f">>> Current: {displayName}\nLast changed: {lastDisplayNameChange}\nChanges: {numberOfDisplayNameChanges}\nUpdatable: {Emoji.CHECKMARK if canUpdateDisplayName == True else Emoji.DENY}", inline=False)
        embed.add_field(name="Login:", value=f">>> Failed Login Attempts: {failedLoginAttempts}\nLast Login: {lastLogin}\nTwo Factor Authentication: {Emoji.CHECKMARK if tfaEnabled == True else Emoji.DENY}", inline=True)
        embed.add_field(name="Country:", value=f"> {country}", inline=False)
        embed.add_field(name="Preferred Language:", value=f"> {preferredLanguage}", inline=False)
        embed.set_footer(text="Bot by Ri524ch")
        await ctx.respond(embed=embed)




@bot.event
async def on_application_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        seconds = convert_seconds(error.retry_after)
        embed = discord.Embed(title="⛔ Error ⛔", description=f"You are on cooldown for `{round(seconds, 1)}` seconds.",color=discord.Color.brand_red())
        await ctx.respond(embed=embed)
    else:
        pass




bot.run(TOKEN)
