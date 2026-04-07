using System;
using System.IO;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Linq;

public class LipSyncCopyVisemes : MonoBehaviour
{
    public OVRLipSyncContextBase lipsyncContext = null;
    public SkinnedMeshRenderer skinnedMeshRenderer = null;

    public int[] visemeToBlendTargets = Enumerable.Range(0, OVRLipSync.VisemeCount).ToArray();

    // NEW: control how strong the mouth movement is
    [Range(50f, 300f)]
    public float visemeStrength = 180f;

    void Update()
    {
        if ((lipsyncContext != null) && (skinnedMeshRenderer != null))
        {
            // get the current viseme frame
            OVRLipSync.Frame frame = lipsyncContext.GetCurrentPhonemeFrame();
            if (frame != null)
            {
                SetVisemeToMorphTarget(frame);
            }
        }
    }

    void SetVisemeToMorphTarget(OVRLipSync.Frame frame)
    {
        for (int i = 0; i < visemeToBlendTargets.Length; i++)
        {
            SafeSetBlendShapeWeight(visemeToBlendTargets[i], frame.Visemes[i]);
        }
    }

    void SafeSetBlendShapeWeight(int blendShapeIdx, float value)
    {
        if (blendShapeIdx != -1 && blendShapeIdx < skinnedMeshRenderer.sharedMesh.blendShapeCount)
        {
            // OVR visemes are 0–1, blendshapes are 0–100
            skinnedMeshRenderer.SetBlendShapeWeight(
                blendShapeIdx,
                value * visemeStrength
            );
        }
    }
}