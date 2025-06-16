from discord_webhook import DiscordWebhook, DiscordEmbed

webhook = ""

sog_non_cdlc_owner_link = "https://drive.google.com/file/d/1bTUDmnRW2amZm7uKz2ShikutPv3aJrKn/view?usp=drive_link"
sog_cdlc_owner_link = "https://drive.google.com/file/d/1TUKsKJuXpNWNIGCUOgtgEAqjPE-kcjPP/view?usp=drive_link"
am2_non_cdlc_owner_link = "https://drive.google.com/file/d/15JpbnAF-R0yej2MILvozztJW76kRz77V/view?usp=drive_link"
am2_cdlc_owner_link = "https://drive.google.com/file/d/1ZlPBnLEzuc42KZoEJwX83yQeekrRvWpJ/view?usp=drive_link"

sog_non_cdlc_owner_link_direct = "https://drive.google.com/uc?export=download&id=1bTUDmnRW2amZm7uKz2ShikutPv3aJrKn"
sog_cdlc_owner_link_direct = "https://drive.google.com/uc?export=download&id=1TUKsKJuXpNWNIGCUOgtgEAqjPE-kcjPP"
am2_non_cdlc_owner_link_direct = "https://drive.google.com/uc?export=download&id=15JpbnAF-R0yej2MILvozztJW76kRz77V"
am2_cdlc_owner_link_direct = "https://drive.google.com/uc?export=download&id=1ZlPBnLEzuc42KZoEJwX83yQeekrRvWpJ"


am2_battalion=[
    [
        "` Battalion`",
        "`     Alpha`",
        "`     Bravo`",
        "`   Charlie`",
        "`       CTC`",
        "`       RHQ`",
        "`       RNR`"
    ],
    [
        "`am2.taw.net` : `2302`",
        "`am2.taw.net` : `2302`",
        "`am2.taw.net` : `2352`",
        "`am2.taw.net` : `2402`",
        "`am2.taw.net` : `2502`",
        "`am2.taw.net` : `2802`",
        "`am2.taw.net` : `2602`",
    ],
    [
        "`AM2`",
        "`AM2`",
        "`AM2`",
        "`AM2`",
        "`AM2`",
        "`AM2`",
        "`AM2`",
    ]
]
am3_battalion=[
    [
        "` Battalion`",
    ],
    [
        "`am3.taw.net` : `2302`",
    ],
    [
        "`AM3`",
    ]
]
vietnam=[
    [
        "` Battalion`",
        "`       RNR`"
    ],
    [
        "`am2.taw.net` : `3302`",
        "`am2.taw.net` : `3602`",
    ],
    [
        "`AM2`",
        "`AM2`",
    ]
]
public=[
    [
        "`     Antistasi #1`",
        "`    Domination #1`",
        "` Frontline Ops #1`",
        "`    Liberation #1`",
        "`    Liberation #2`"
    ],
    [
        "`am2.taw.net` : `4002`",
        "`am2.taw.net` : `4102`",
        "`am2.taw.net` : `4302`",
        "`am2.taw.net` : `4202`",
        "`am2.taw.net` : `4252`",
    ],
    [
        "`AM2`",
        "`AM2`",
        "`AM2`",
        "`AM2`",
        "`AM2`",
    ]
]

if __name__ == "__main__":

    am2ModpackEmbed= DiscordEmbed(title="AM2 Battalion Modpack", url="https://steamcommunity.com/sharedfiles/filedetails/?id=2293037577", description="You can subscribe to our main battalion modpack here, or you can load in the the `html` presets directly into your launcher. If you do not own the Western Sahara CDLC just install the compatibility patch which is included in the non-cdlc owner specific preset.", color='ffffff')
    am2ModpackEmbed.set_thumbnail(url="https://images.steamusercontent.com/ugc/51327907334009040/3EAB035EBBAD140042391A73540A267ACF29999C/?imw=268&imh=268&ima=fit&impolicy=Letterbox&imcolor=%23000000&letterbox=true")
    am2ModpackEmbed.add_embed_field(name="HTML Presets", value=f"[AM2 CDLC Owner]({am2_cdlc_owner_link_direct})\n[AM2 Non-CDLC Owner]({am2_non_cdlc_owner_link_direct}) ", inline=True)

    vietnamModpackEmbed= DiscordEmbed(title="Vietnam Modpack", url="https://steamcommunity.com/sharedfiles/filedetails/?id=3410913034", description="You can subscribe to our vietnam modpack here, or you can load in the the `html` presets directly into your launcher. If you do not own the S.O.G. Prairie Fire CDLC just install the compatibility patch which is included in the non-cdlc owner specific preset.", color='ffffff')
    vietnamModpackEmbed.set_thumbnail(url="https://images.steamusercontent.com/ugc/51330444024947030/8B24785D05EFBD76DFA2F7695B7CB1342BB90EC6/?imw=268&imh=268&ima=fit&impolicy=Letterbox&imcolor=%23000000&letterbox=true")
    vietnamModpackEmbed.add_embed_field(name="HTML Presets", value=f"[Vietnam CDLC Owner]({sog_cdlc_owner_link_direct})\n[Vietnam Non-CDLC Owner]({sog_cdlc_owner_link_direct}k) ", inline=True)

    am2ServersEmbed = DiscordEmbed(title='AM2 Main Servers', description='', color='ffffff')
    am2ServersEmbed.add_embed_field(name="SERVER", value="\n".join(am2_battalion[0]))
    am2ServersEmbed.add_embed_field(name="IP : PORT", value="\n".join(am2_battalion[1]))
    am2ServersEmbed.add_embed_field(name="PASSWORD", value="\n".join(am2_battalion[2]))

    am3ServersEmbed = DiscordEmbed(title='AM3 Main Servers', description='', color='ffffff')
    am3ServersEmbed.add_embed_field(name="SERVER", value="\n".join(am3_battalion[0]))
    am3ServersEmbed.add_embed_field(name="IP : PORT", value="\n".join(am3_battalion[1]))
    am3ServersEmbed.add_embed_field(name="PASSWORD", value="\n".join(am3_battalion[2]))

    vietnamServersEmbed = DiscordEmbed(title='Vietnam Servers', description='', color='ffffff')
    vietnamServersEmbed.add_embed_field(name="SERVER", value="\n".join(vietnam[0]))
    vietnamServersEmbed.add_embed_field(name="IP : PORT", value="\n".join(vietnam[1]))
    vietnamServersEmbed.add_embed_field(name="PASSWORD", value="\n".join(vietnam[2]))

    publicServersEmbed = DiscordEmbed(title='Fun Servers', description='', color='ffffff')
    publicServersEmbed.add_embed_field(name="SERVER", value="\n".join(public[0]))
    publicServersEmbed.add_embed_field(name="IP : PORT", value="\n".join(public[1]))
    publicServersEmbed.add_embed_field(name="PASSWORD", value="\n".join(public[2]))


    battalionHook = DiscordWebhook(url=webhook)
    battalionHook.add_embed(am2ModpackEmbed)
    battalionHook.add_embed(am2ServersEmbed)
    battalionHook.add_embed(am3ServersEmbed)
    battalionHookResponse = battalionHook.execute()

    battalionHook = DiscordWebhook(url=webhook)
    battalionHook.add_embed(vietnamModpackEmbed)
    battalionHook.add_embed(vietnamServersEmbed)
    battalionHookResponse = battalionHook.execute()

    battalionHook = DiscordWebhook(url=webhook)
    battalionHook.add_embed(publicServersEmbed)
    battalionHookResponse = battalionHook.execute()
