from discord_webhook import DiscordWebhook, DiscordEmbed

battalion2=[
    [
        "`      Main`",
        "`       CTC`",
        "`       RHQ`",
        "`       RNR`",
        "`  Training`",
    ],
    [
        "`65.109.109.94` `:` `2402`", 
        "`65.109.109.94` `:` `2502`",
        "`65.109.109.94` `:` `2602`",
        "`65.109.109.94` `:` `2702`",
        "`65.109.109.94` `:` `2902`",
    ],
    [
        "[battalion](https://drive.google.com/uc?export=download&id=1BVjZYwM_3GHlH_7qFVbqNmCavkm5OgAz) `|` [clientside](https://drive.google.com/uc?export=download&id=11rULjxZu9TuJR8L3tShryInZTFroXHz1)",
        "[battalion](https://drive.google.com/uc?export=download&id=1BVjZYwM_3GHlH_7qFVbqNmCavkm5OgAz) `|` [clientside](https://drive.google.com/uc?export=download&id=11rULjxZu9TuJR8L3tShryInZTFroXHz1)",
        "[battalion](https://drive.google.com/uc?export=download&id=1BVjZYwM_3GHlH_7qFVbqNmCavkm5OgAz) `|` [clientside](https://drive.google.com/uc?export=download&id=11rULjxZu9TuJR8L3tShryInZTFroXHz1)",
        "[battalion](https://drive.google.com/uc?export=download&id=1BVjZYwM_3GHlH_7qFVbqNmCavkm5OgAz) `|` [clientside](https://drive.google.com/uc?export=download&id=11rULjxZu9TuJR8L3tShryInZTFroXHz1)",
        "[battalion](https://drive.google.com/uc?export=download&id=1BVjZYwM_3GHlH_7qFVbqNmCavkm5OgAz) `|` [clientside](https://drive.google.com/uc?export=download&id=11rULjxZu9TuJR8L3tShryInZTFroXHz1)",
    ],
]

public=[
    [
        "`Teamspeak`",
        "`Mike Force`",
        "`Antistasi: SOG`",
        "`Escape From Arma`",
    ],
    [
        "`65.109.109.94` `:` `-`", 
        "`65.109.109.94` `:` `2382`", 
        "`65.109.109.94` `:` `2382`", 
        "`65.109.109.94` `:` `2322`", 
    ],
    [
        "- `|` -",
        "[sog](https://drive.google.com/uc?export=download&id=17NYeP9zsF-KI2gFpSiHQ7w_sSS1ego0J) `|` [clientside]()",
        "[antistasi_sog](https://drive.google.com/uc?export=download&id=1rhjNOxESzvLGTf7qXhZHwSIMYTv5RqTP) `|` [clientside]()",
        "[eft](https://drive.google.com/file/d/1yVJUBaSTVAn2lyP2iIDyzFDijk-zM9zu/view?usp=sharing) `|` [clientside]()",
    ],

]

if __name__ == "__main__":
    
    battalionEmbed = DiscordEmbed(title='MAIN SERVERS', description='You can download either the html preset listed below to play on these servers or load the [community pack](https://steamcommunity.com/sharedfiles/filedetails/?id=2840862835) and load all dependencies with it. All mods inside the clientside preset are optional and their bikeys have also been accepted on the server.', color='ffffff')
    battalionEmbed.add_embed_field(name="SERVER", value="\n".join(battalion2[0]))
    battalionEmbed.add_embed_field(name="IP : PORT", value="\n".join(battalion2[1]))
    battalionEmbed.add_embed_field(name="MODS", value="\n".join(battalion2[2]))

    publicEmbed = DiscordEmbed(title='PUBLIC SERVERS', description='Come hang out on our public servers, no mods should be required to join!', color='ffffff')
    publicEmbed.add_embed_field(name="SERVER", value="\n".join(public[0]))
    publicEmbed.add_embed_field(name="IP : PORT", value="\n".join(public[1]))
    publicEmbed.add_embed_field(name="MODS", value="\n".join(public[2]))

    battalionHook = DiscordWebhook(url="https://discord.com/api/webhooks/1001978810390040647/3mfkDsqRxk5QWPkLKMEdUORLOikHKcD3F_hIvZ-Ynu119M9P-IHm0Ll8ClRi3RXf6KlB")
    battalionHook.add_embed(battalionEmbed)
    battalionHook.add_embed(publicEmbed)
    battalionHookResponse = battalionHook.execute()
