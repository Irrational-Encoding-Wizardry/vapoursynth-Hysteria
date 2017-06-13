#####################################################
#                                                   #
# Hysteria, a line darkening script by Scintilla    #
# Last updated 9/11/10                              #
#                                                   #
#####################################################
#
# Syntax:
# Hysteria(clip, strength= 1.0, usemask=True, lowthresh=6, highthresh=20, luma_cap=191, maxchg=255, minchg=0, planes = [0], luma=True, showmask=False)
#
# Requires YV12 input, frame-based only.  Is reasonably fast.
# Suggestions for improvement welcome: scintilla@aquilinestudios.org
#
# Required plugins:
# MaskTools 2.0 (MT_MaskTools)
#
# Arguments:
#
# strength (default=1.0) - This is a multiplicative factor for the amounts
#	by which the pixels are darkened.  Ordinarily, each pixel is
#	darkened by the difference between its luma value and the average
#	luma value of its brighter spatial neighbours.  So if you want more
#	darkening, increase this value.
#
# usemask (default=true) - Whether or not to apply the mask.  If false,
#	the entire image will have its edges darkened instead of just the
#	edges detected in the mask.  Could be useful on some sources
#	(specifically, it will often make dark lines look thicker), but
#	you will probably want to stick to lower values of strength if you
#	choose to go that route.
#
# lowthresh (default=6) - This is the threshold used for the noisy mask.
#	Increase this value if your mask is picking up too much noise
#	around the edges, or decrease it if the mask is not being grown
#	thick enough to cover all of each edge.
#
# highthresh (default=20) - This is the threshold used for the clean mask.
#	Increase this value if your mask is picking up too many weaker
#	edges, or decrease it if the mask is not picking up enough.
#
# luma_cap (default=191) - An idea swiped from FLD/VMToon.  Any pixels
#	brighter than this value will not be darkened at all, no matter
#	what the rest of the parameters are.  This is useful if you have
#	lighter edges that you do not want darkened.  0 will result in
#	no darkening at all, while 255 will turn off the cap.
#
# maxchg (default=255) - No pixel will be darkened by more than this
#	amount, no matter how high you set the strength parameter.
#	This can be useful if you want to darken your weaker lines more
#	without going overboard on the stronger ones.  0 will result in
#	no darkening at all, while 255 (the default) will turn off the
#	limiting.
#
# minchg (default=0) - Another idea swiped from FLD/VMToon (though in
#	those functions it was called "threshold").  Any pixels that
#	would have been darkened by less than this amount will instead
#	not be darkened at all.  This can be useful if you have noise
#	that is getting darkened slightly.  0 (the default) will turn
#	off the thresholding, while 255 will result in no darkening at all.
# 
# planes (default=0) - Luma plane
#
# luma (default=True) - Use luma plane for masking
#    
# showmask (default=false) - When true, the function will display the
#	current edge mask plus the chroma from the original image.
#	Use this to find the optimal values of lowthresh and highthresh.
#
###################
#
# Changelog:
#
# 9/11/10: Is this thing on?
#
###################


import vapoursynth as vs

def scale(old_value, new_bd=16):
    return int((old_value * ((1 << new_bd) - 1)) / 255)
	
def hysteria(clip, strength= 1.0, usemask=True, lowthresh=6, highthresh=20, luma_cap=191, maxchg=255, minchg=0, planes = [0], luma=True, showmask=False):
				
    core = vs.get_core()
	
    if not isinstance(clip, vs.VideoNode):
        raise ValueError('This is not a clip')
	
    # This scales the values parameters of Levels
    if clip.format.bits_per_sample != 8:
        max_in = (1 << clip.format.bits_per_sample) - 1
        max_out = (1 << clip.format.bits_per_sample) - 1
        min_out = scale(80, clip.format.bits_per_sample)
		
    # Medium value
    mid =  (2 ** clip.format.bits_per_sample) // 2

		
    noisymask = core.std.Sobel(clip, min=lowthresh, max=lowthresh, planes=planes, rshift=0)
    cleanmask = core.std.Sobel(clip, min=highthresh, max=highthresh, planes=planes, rshift=0)
	
    themask = core.generic.Hysteresis(cleanmask,noisymask)
    themask = core.std.Inflate(themask)
    themask = core.generic.Blur(themask, ratio_h=1.0)
    themask = core.generic.Blur(themask, ratio_h=1.0)
    themask = core.std.Deflate(themask)
	
    clipa = core.std.Inflate(clip, planes=[0])
    diffs = core.std.MakeDiff(clipa,clip)
    diffs = core.std.Expr([diffs], ['x {mid} - {strength} *'.format(strength=strength, mid=mid)])

    darkened = core.std.Expr([clip, diffs], ['x x {luma_cap} > 0 y {maxchg} > {maxchg} y {minchg} < 0 y ? ? ? -'.format(luma_cap=luma_cap,maxchg=maxchg,minchg=minchg)])

    if usemask:
        themask = core.std.ShufflePlanes(themask, planes=[0], colorfamily=vs.GRAY)
        final = core.std.MaskedMerge(clip,darkened,themask, planes=planes, first_plane=luma)
    else:
        final = core.std.ShufflePlanes(clips=[darkened,clip], planes=[0, 1, 2], colorfamily=vs.YUV)

    if showmask:
        mascara = core.std.Levels(themask, min_in=0, max_in=max_in, gamma=1.0, min_out=min_out, max_out=max_out)
        mascara = core.std.ShufflePlanes([mascara,clip], planes=[0,1,2], colorfamily=vs.YUV)
        return mascara

    return final