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
        "`78.46.78.85` `:` `2402`", 
        "`78.46.78.85` `:` `2502`",
        "`78.46.78.85` `:` `2602`",
        "`78.46.78.85` `:` `2702`",
        "`78.46.78.85` `:` `2902`",
    ],
    [
        "[battalion](https://drive.google.com/uc?export=download&id=1rCAEv16GV_TnO8dSBEG5QfqO53uOMeei) `|` [clientside](https://drive.google.com/uc?export=download&id=11rULjxZu9TuJR8L3tShryInZTFroXHz1)",
        "[battalion](https://drive.google.com/uc?export=download&id=1rCAEv16GV_TnO8dSBEG5QfqO53uOMeei) `|` [clientside](https://drive.google.com/uc?export=download&id=11rULjxZu9TuJR8L3tShryInZTFroXHz1)",
        "[battalion](https://drive.google.com/uc?export=download&id=1rCAEv16GV_TnO8dSBEG5QfqO53uOMeei) `|` [clientside](https://drive.google.com/uc?export=download&id=11rULjxZu9TuJR8L3tShryInZTFroXHz1)",
        "[battalion](https://drive.google.com/uc?export=download&id=1rCAEv16GV_TnO8dSBEG5QfqO53uOMeei) `|` [clientside](https://drive.google.com/uc?export=download&id=11rULjxZu9TuJR8L3tShryInZTFroXHz1)",
        "[battalion](https://drive.google.com/uc?export=download&id=1rCAEv16GV_TnO8dSBEG5QfqO53uOMeei) `|` [clientside](https://drive.google.com/uc?export=download&id=11rULjxZu9TuJR8L3tShryInZTFroXHz1)",
    ],
]

legion4=[
    [
        "`      Main`",
        "`       CTC`",
        "`       RHQ`",
        "`       RNR`",
    ],
    [
        "`78.46.78.85` `:` `4402`", 
        "`78.46.78.85` `:` `4502`",
        "`78.46.78.85` `:` `4602`",
        "`78.46.78.85` `:` `4702`",
    ],
    [
        "[legion](https://drive.google.com/uc?export=download&id=1w_M99bxN59GdQJI2NURBpKm4pMQ3X-C-) `|` [clientside](https://drive.google.com/uc?export=download&id=1F5vjZG-yD_HfmmT1noAbfJ5VGQDEUE3e)",
        "[legion](https://drive.google.com/uc?export=download&id=1w_M99bxN59GdQJI2NURBpKm4pMQ3X-C-) `|` [clientside](https://drive.google.com/uc?export=download&id=1F5vjZG-yD_HfmmT1noAbfJ5VGQDEUE3e)",
        "[legion](https://drive.google.com/uc?export=download&id=1w_M99bxN59GdQJI2NURBpKm4pMQ3X-C-) `|` [clientside](https://drive.google.com/uc?export=download&id=1F5vjZG-yD_HfmmT1noAbfJ5VGQDEUE3e)",
        "[legion](https://drive.google.com/uc?export=download&id=1w_M99bxN59GdQJI2NURBpKm4pMQ3X-C-) `|` [clientside](https://drive.google.com/uc?export=download&id=1F5vjZG-yD_HfmmT1noAbfJ5VGQDEUE3e)",
    ],
]

public=[
    [
        "`Domination`",
    ],
    [
        "`78.46.78.85` `:` `2302`", 
    ],
    [
        "- `|` -",

    ],
]

if __name__ == "__main__":
    
    battalionEmbed = DiscordEmbed(title='2ND BATTALION SERVERS (EU)', description='[Join our semi-milsim unit!](https://discord.gg/qP2AwVhs) \n\nYou can download either the html preset listed below to play on these servers or load the [community pack](https://steamcommunity.com/sharedfiles/filedetails/?id=2841184293) and load all dependencies with it. All mods inside the clientside preset are optional and their bikeys have also been accepted on the server.', color='ffffff')
    battalionEmbed.add_embed_field(name="SERVER", value="\n".join(battalion2[0]))
    battalionEmbed.add_embed_field(name="IP` : PORT", value="\n".join(battalion2[1]))
    battalionEmbed.add_embed_field(name="MODS", value="\n".join(battalion2[2]))

    legionEmbed = DiscordEmbed(title='4TH LEGION SERVERS (STARWARS)', description='[Join our starwars unit!](https://discord.gg/braExgyyzx) \n\nYou can download either the html preset listed below to play on these servers or load the [community pack](https://steamcommunity.com/sharedfiles/filedetails/?id=2840861814) and load all dependencies with it. All mods inside the clientside preset are optional and their bikeys have also been accepted on the server.', color='ffffff')
    legionEmbed.add_embed_field(name="SERVER", value="\n".join(legion4[0]))
    legionEmbed.add_embed_field(name="IP : PORT", value="\n".join(legion4[1]))
    legionEmbed.add_embed_field(name="MODS", value="\n".join(legion4[2]))

    publicEmbed = DiscordEmbed(title='GEG PUBLIC SERVERS', description='[Join the main GEG discord.](https://discord.gg/kaeCF7snmk) \n\nCome hang out on our public servers, no mods should be required to join!', color='ffffff')
    publicEmbed.add_embed_field(name="SERVER", value="\n".join(public[0]))
    publicEmbed.add_embed_field(name="IP : PORT", value="\n".join(public[1]))
    publicEmbed.add_embed_field(name="MODS", value="\n".join(public[2]))

    battalionHook = DiscordWebhook(url="https://discord.com/api/webhooks/1001978810390040647/3mfkDsqRxk5QWPkLKMEdUORLOikHKcD3F_hIvZ-Ynu119M9P-IHm0Ll8ClRi3RXf6KlB")
    battalionHook.add_embed(battalionEmbed)
    battalionHook.add_embed(legionEmbed)
    battalionHook.add_embed(publicEmbed)
    battalionHookResponse = battalionHook.execute()

    legionHook = DiscordWebhook(url="https://discord.com/api/webhooks/1002137743721250846/ppOWWa015d3wa43rX8MhcfTVtT8z3CIZZdzah6uZmea1DNSlZNY2DDWdVatUTRaClJoJ")
    legionHook.add_embed(legionEmbed)
    legionHook.add_embed(battalionEmbed)
    legionHook.add_embed(publicEmbed)
    legionHookResponse = legionHook.execute()